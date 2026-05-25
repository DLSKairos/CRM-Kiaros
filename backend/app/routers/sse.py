"""
SSE endpoint — transmite eventos del pipeline en tiempo real.

GET /runs/{run_id}/stream  → text/event-stream
Cada evento tiene formato estándar SSE:
    data: {"event": "step_done", "data": {...}}\n\n
"""

import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings

router = APIRouter(prefix="/runs", tags=["sse"])


async def _event_generator(request: Request, run_id: str):
    """
    Suscribe al canal Redis del run y reenvía eventos como SSE al cliente.
    Termina cuando:
    - El cliente cierra la conexión
    - Se recibe un evento 'completed' o 'failed'
    - Timeout de 10 minutos sin actividad
    """
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    channel = f"run:{run_id}"

    await pubsub.subscribe(channel)

    # Heartbeat cada 20s para mantener la conexión viva
    last_event_time = asyncio.get_event_loop().time()
    timeout = 600  # 10 minutos

    try:
        yield f"data: {json.dumps({'event': 'connected', 'data': {'run_id': run_id}})}\n\n"

        while True:
            # Verificar si el cliente se desconectó
            if await request.is_disconnected():
                break

            # Timeout por inactividad
            now = asyncio.get_event_loop().time()
            if now - last_event_time > timeout:
                yield f"data: {json.dumps({'event': 'timeout', 'data': {'message': 'Connection timeout'}})}\n\n"
                break

            # Leer mensaje del canal con timeout corto
            message = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True),
                timeout=1.0,
            ) if not await request.is_disconnected() else None

            if message and message.get("type") == "message":
                data = message.get("data", "")
                last_event_time = asyncio.get_event_loop().time()
                yield f"data: {data}\n\n"

                # Terminar si el pipeline completó o falló
                try:
                    parsed = json.loads(data)
                    if parsed.get("event") in ("completed", "failed"):
                        break
                except (json.JSONDecodeError, AttributeError):
                    pass

            else:
                # Heartbeat
                elapsed = asyncio.get_event_loop().time() - last_event_time
                if elapsed > 20:
                    yield f": heartbeat\n\n"
                    last_event_time = asyncio.get_event_loop().time()
                await asyncio.sleep(0.1)

    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await r.aclose()


@router.get("/{run_id}/stream")
async def stream_run(run_id: str, request: Request):
    """Transmite eventos del pipeline en tiempo real via Server-Sent Events."""
    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="run_id debe ser un UUID válido")

    return StreamingResponse(
        _event_generator(request, run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
