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


def _web_search(query: str, max_chars: int = 6000) -> str:
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query, "kl": "co-es"},
                headers=_HEADERS_BROWSER,
            )
            resp.raise_for_status()
            return _strip_html(resp.text, max_chars=max_chars)
    except Exception as exc:
        return f"[web_search error] {exc}"


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
    # Máximo de tool calls por ejecución — evita bucles infinitos con Groq
    max_tool_calls: int = 12
    # Tamaño máximo de contenido web enviado al LLM (Groq tiene límites de tokens más ajustados)
    _groq_max_chars_search: int = 2000
    _groq_max_chars_fetch: int = 2500

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

                    # Si superó el límite, forzar respuesta final con lo que tiene
                    if tool_calls_count >= self.max_tool_calls:
                        messages.append({
                            "role": "user",
                            "content": (
                                "Has usado suficientes búsquedas. "
                                "Devuelve AHORA el JSON final con los datos que encontraste. "
                                "No hagas más búsquedas."
                            ),
                        })
                    continue

                raise ValueError(f"finish_reason inesperado: {choice['finish_reason']}")

    def _groq_post(self, client: httpx.Client, messages: list[dict]) -> httpx.Response:
        """POST a Groq con retry automático para 429 (rate limit) y 413 (payload)."""
        for attempt in range(6):
            resp = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.groq_model,
                    "messages": messages,
                    "tools": _TOOLS_OPENAI,
                    "tool_choice": "auto",
                    "max_tokens": self.max_tokens,
                    "temperature": 0.3,
                },
            )
            if resp.status_code == 429:
                # Respetar Retry-After si viene en el header, si no usar backoff
                retry_after = int(resp.headers.get("retry-after", min(60, 5 * (attempt + 1))))
                time.sleep(retry_after)
                continue
            if resp.status_code == 413:
                # Contexto demasiado grande — truncar los tool results más viejos
                messages = self._trim_groq_context(messages)
                time.sleep(2)
                continue
            resp.raise_for_status()
            return resp
        raise RuntimeError("Groq sigue devolviendo rate limit tras 6 intentos")

    @staticmethod
    def _trim_groq_context(messages: list[dict]) -> list[dict]:
        """Reduce el tamaño del contexto truncando tool results antiguos al 50%."""
        trimmed = []
        for msg in messages:
            if msg.get("role") == "tool" and isinstance(msg.get("content"), str):
                msg = {**msg, "content": msg["content"][: len(msg["content"]) // 2] + "...[truncado]"}
            trimmed.append(msg)
        return trimmed
