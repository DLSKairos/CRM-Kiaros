import json
import re
import time
from abc import ABC, abstractmethod

import httpx
from anthropic import Anthropic, APIError, APITimeoutError

from app.config import settings

_HEADERS_BROWSER = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# ─── Tools en formato Anthropic ───────────────────────────────────────────────

_TOOLS_ANTHROPIC = [
    {
        "name": "web_search",
        "description": (
            "Busca en la web información sobre empresas, contactos y directorios colombianos. "
            "Usa queries específicos. Devuelve extracto del HTML de resultados de búsqueda."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Consulta de búsqueda"}},
            "required": ["query"],
        },
    },
    {
        "name": "web_fetch",
        "description": (
            "Descarga el contenido de una URL. Útil para leer páginas de empresas, "
            "directorios sectoriales y perfiles de LinkedIn. Devuelve el texto de la página."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL a visitar"}},
            "required": ["url"],
        },
    },
]

# ─── Tools en formato OpenAI / Groq ───────────────────────────────────────────

_TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Busca en la web información sobre empresas, contactos y directorios colombianos. "
                "Devuelve extracto del HTML de resultados de búsqueda."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Consulta de búsqueda"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Descarga el contenido de una URL. Útil para leer páginas de empresas "
                "y directorios sectoriales."
            ),
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL a visitar"}},
                "required": ["url"],
            },
        },
    },
]


# ─── Utilidades web ───────────────────────────────────────────────────────────

def _strip_html(html: str, max_chars: int = 8000) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _web_search_tavily(query: str, max_chars: int) -> str:
    """Búsqueda via Tavily API. Lanza excepción si falla."""
    with httpx.Client(timeout=20) as client:
        resp = client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 8,
                "include_raw_content": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        lines = [
            f"[{r.get('title','')}] {r.get('url','')} — {r.get('content','')}"
            for r in data.get("results", [])
        ]
        return "\n\n".join(lines)[:max_chars]


def _web_search_duckduckgo(query: str, max_chars: int) -> str:
    """Búsqueda via DuckDuckGo HTML (sin API key). Lanza excepción si falla."""
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        resp = client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={**_HEADERS_BROWSER, "Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        # Extraer resultados: título + URL + snippet
        html = resp.text
        results = re.findall(
            r'class="result__title"[^>]*>.*?href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'class="result__snippet"[^>]*>(.*?)</span>',
            html, re.DOTALL
        )
        if not results:
            # Fallback: extraer cualquier link con texto visible
            links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]{10,})</a>', html)
            lines = [f"{text.strip()} — {url}" for url, text in links[:10]]
        else:
            lines = [
                f"[{re.sub('<[^>]+>', '', title).strip()}] {url} — {re.sub('<[^>]+>', '', snippet).strip()}"
                for url, title, snippet in results[:8]
            ]
        return "\n\n".join(lines)[:max_chars]


def _web_search(query: str, max_chars: int = 6000) -> str:
    """Busca con Tavily; si falla, usa DuckDuckGo como fallback automático."""
    # Intentar Tavily primero si hay API key configurada
    if settings.tavily_api_key:
        try:
            return _web_search_tavily(query, max_chars)
        except Exception:
            pass  # Fallback a DuckDuckGo

    # DuckDuckGo como fallback (o primario si no hay Tavily key)
    try:
        return _web_search_duckduckgo(query, max_chars)
    except Exception as exc:
        return f"[web_search error] Tavily y DuckDuckGo fallaron: {exc}"


def _web_fetch(url: str, max_chars: int = 8000) -> str:
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            resp = client.get(url, headers=_HEADERS_BROWSER)
            resp.raise_for_status()
            return _strip_html(resp.text, max_chars=max_chars)
    except Exception as exc:
        return f"[web_fetch error] {exc}"


def _run_tool(name: str, tool_input: dict, max_chars_search: int = 6000, max_chars_fetch: int = 8000) -> str:
    if name == "web_search":
        return _web_search(tool_input["query"], max_chars=max_chars_search)
    if name == "web_fetch":
        return _web_fetch(tool_input["url"], max_chars=max_chars_fetch)
    return f"[error] herramienta desconocida: {name}"


# ─── Parser JSON ──────────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | list:
    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if m:
        return json.loads(m.group(1))
    raise ValueError(f"No se encontró JSON en la respuesta: {text[:300]}")


# ─── Base agent ───────────────────────────────────────────────────────────────

class AgentBase(ABC):
    """
    Base para todos los agentes de SEÑAL.

    Soporta dos proveedores configurados via AI_PROVIDER en .env:
      - "anthropic": usa Claude (Haiku o Sonnet según el agente, pago por tokens)
      - "groq":      usa Llama 3.3 70B via Groq API (gratuito, OpenAI-compatible)

    Cada subclase declara:
      anthropic_model: str   — modelo a usar cuando AI_PROVIDER=anthropic
      groq_model: str        — modelo a usar cuando AI_PROVIDER=groq
    """

    # Subclases sobrescriben estos valores
    anthropic_model: str = "claude-haiku-4-5-20251001"
    groq_model: str = "llama-3.3-70b-versatile"

    max_tokens: int = 4096
    max_retries: int = 5
    max_tool_calls: int = 12
    # Límites bajos para no llegar al 413 Payload Too Large de Groq
    _groq_max_chars_search: int = 800
    _groq_max_chars_fetch: int = 1000

    def __init__(self) -> None:
        self._provider = settings.ai_provider.lower()
        if self._provider == "anthropic":
            self._anthropic = Anthropic(api_key=settings.anthropic_api_key)
        elif self._provider == "groq":
            if not settings.groq_api_key:
                raise RuntimeError("AI_PROVIDER=groq pero GROQ_API_KEY no está configurado")
        else:
            raise RuntimeError(f"AI_PROVIDER inválido: '{self._provider}'. Usa 'anthropic' o 'groq'")

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def run(self, user_message: str) -> dict | list:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                if self._provider == "anthropic":
                    return self._loop_anthropic(user_message)
                else:
                    return self._loop_groq(user_message)
            except (APIError, APITimeoutError, ValueError, Exception) as exc:
                last_exc = exc
                if attempt < self.max_retries - 1:
                    wait = min(60, 4 ** attempt)
                    time.sleep(wait)
        raise RuntimeError(f"Falló tras {self.max_retries} intentos: {last_exc}") from last_exc

    # ── Anthropic loop ────────────────────────────────────────────────────────

    def _loop_anthropic(self, user_message: str) -> dict | list:
        messages: list[dict] = [{"role": "user", "content": user_message}]
        tool_calls_count = 0

        while True:
            response = self._anthropic.messages.create(
                model=self.anthropic_model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                tools=_TOOLS_ANTHROPIC,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return _extract_json(block.text)
                raise ValueError("Respuesta sin bloque de texto")

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_calls_count += 1
                        result = _run_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "user", "content": tool_results})
                if tool_calls_count >= self.max_tool_calls:
                    messages.append({
                        "role": "user",
                        "content": (
                            "Has usado suficientes búsquedas. "
                            "Devuelve AHORA el JSON final con los datos que encontraste."
                        ),
                    })
                continue

            raise ValueError(f"stop_reason inesperado: {response.stop_reason}")

    # ── Groq loop (OpenAI-compatible) ─────────────────────────────────────────

    def _loop_groq(self, user_message: str) -> dict | list:
        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        tool_calls_count = 0

        with httpx.Client(timeout=60) as client:
            while True:
                # Retry interno para 429 y 413 de Groq
                resp = self._groq_post(client, messages)
                data = resp.json()
                choice = data["choices"][0]
                msg = choice["message"]

                messages.append(msg)

                if choice["finish_reason"] == "stop":
                    return _extract_json(msg.get("content") or "")

                if choice["finish_reason"] == "tool_calls":
                    tool_calls_count += len(msg.get("tool_calls", []))
                    tool_results = []
                    for tc in msg.get("tool_calls", []):
                        fn = tc["function"]
                        tool_input = json.loads(fn["arguments"])
                        result = _run_tool(
                            fn["name"],
                            tool_input,
                            max_chars_search=self._groq_max_chars_search,
                            max_chars_fetch=self._groq_max_chars_fetch,
                        )
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": result,
                        })
                    messages.extend(tool_results)

                    # Límite alcanzado: forzar respuesta final deshabilitando tools
                    if tool_calls_count >= self.max_tool_calls:
                        resp_final = self._groq_post(client, messages, tool_choice="none")
                        final_content = resp_final.json()["choices"][0]["message"].get("content", "")
                        return _extract_json(final_content)

                    continue

                raise ValueError(f"finish_reason inesperado: {choice['finish_reason']}")

    def _groq_post(self, client: httpx.Client, messages: list[dict], tool_choice: str = "auto") -> httpx.Response:
        """POST a Groq con retry automático para 429 (rate limit) y 413 (payload)."""
        payload: dict = {
            "model": self.groq_model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.3,
        }
        if tool_choice == "none":
            # Sin tools — forzar respuesta de texto puro
            payload["tool_choice"] = "none"
        else:
            payload["tools"] = _TOOLS_OPENAI
            payload["tool_choice"] = "auto"
            # Una herramienta por turno: evita que el modelo pida 20 búsquedas
            # simultáneas que inundan el contexto y causan 413 Payload Too Large
            payload["parallel_tool_calls"] = False

        last_status: int | None = None
        for attempt in range(6):
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code == 429:
                # Cap en 90s: Groq free tier puede mandar retry-after de minutos/horas
                # cuando agota el límite diario de tokens — sin cap, el worker duerme
                # 17+ minutos sin avisarle nada al frontend ni al usuario.
                raw_retry = int(resp.headers.get("retry-after", 5 * (attempt + 1)))
                retry_after = min(raw_retry, 90)
                last_status = resp.status_code
                # Si el retry-after real era muy largo, es límite diario — fallar rápido
                if raw_retry > 90:
                    raise RuntimeError(
                        f"Límite diario de tokens de Groq alcanzado "
                        f"(retry-after={raw_retry}s ≈ {raw_retry//60}min). "
                        f"Espera a mañana o cambia AI_PROVIDER=anthropic en .env"
                    )
                time.sleep(retry_after)
                continue
            if resp.status_code == 413:
                # Eliminar los tool results más viejos completos (no truncar)
                messages = self._trim_groq_context(messages)
                payload["messages"] = messages
                last_status = resp.status_code
                time.sleep(2)
                continue
            resp.raise_for_status()
            time.sleep(10)  # cooldown preventivo: Groq free tier necesita ~25-30s para recuperar
            return resp
        raise RuntimeError(f"Groq no respondió tras 6 intentos (último status HTTP: {last_status})")

    @staticmethod
    def _trim_groq_context(messages: list[dict]) -> list[dict]:
        """Reduce el contexto en dos pasos para resolver 413 Payload Too Large.

        Paso 1: trunca el contenido de TODOS los tool results a 300 chars.
        Paso 2: si el contexto sigue siendo grande, elimina los tool result+assistant
                pairs más viejos (50% de los existentes).
        Esto preserva la historia de qué herramientas se llamaron pero reduce
        drásticamente el payload enviado a Groq.
        """
        # Paso 1: truncar contenido de todos los tool results
        trimmed = []
        for m in messages:
            if m.get("role") == "tool" and isinstance(m.get("content"), str) and len(m["content"]) > 300:
                m = {**m, "content": m["content"][:300] + "…[truncado]"}
            trimmed.append(m)

        # Estimar tamaño aproximado
        total_chars = sum(len(str(m.get("content", ""))) for m in trimmed)
        if total_chars <= 40_000:
            return trimmed

        # Paso 2: eliminar el 50% más viejo de pares assistant+tool
        tool_indices = [i for i, m in enumerate(trimmed) if m.get("role") == "tool"]
        if not tool_indices:
            return trimmed

        to_remove = max(1, len(tool_indices) // 2)
        indices_to_drop = set(tool_indices[:to_remove])
        first_drop = min(indices_to_drop)
        if first_drop > 0 and trimmed[first_drop - 1].get("role") == "assistant":
            indices_to_drop.add(first_drop - 1)
        return [m for i, m in enumerate(trimmed) if i not in indices_to_drop]
