"""
Notificaciones al terminar un pipeline run.
- Slack: webhook con resumen de resultados
- Resend (email): envío al equipo comercial
Ambas son opcionales — si falta la config, se omiten silenciosamente.
"""

import json
from datetime import datetime

import httpx

from app.config import settings


def notify_run_completed(
    *,
    run_id: str,
    sector: str,
    ciudad: str,
    calientes: int,
    tibios: int,
    frios: int,
    excel_path: str,
) -> None:
    """Envía notificaciones de run completado. Fire-and-forget (no lanza excepciones)."""
    _notify_slack(run_id=run_id, sector=sector, ciudad=ciudad, calientes=calientes, tibios=tibios, frios=frios, excel_path=excel_path)
    _notify_email(run_id=run_id, sector=sector, ciudad=ciudad, calientes=calientes, tibios=tibios, frios=frios)


def _notify_slack(*, run_id: str, sector: str, ciudad: str, calientes: int, tibios: int, frios: int, excel_path: str) -> None:
    if not settings.slack_webhook_url:
        return
    total = calientes + tibios + frios
    text = (
        f":signal_strength: *SEÑAL — Pipeline completado* ({datetime.now().strftime('%d/%m/%Y %H:%M')})\n"
        f">*Sector:* {sector} | *Ciudad:* {ciudad}\n"
        f">*Total leads:* {total} | :green_circle: {calientes} calientes | :yellow_circle: {tibios} tibios | :white_circle: {frios} fríos\n"
        f">*Run ID:* `{run_id}`\n"
        f">*Excel:* `{excel_path}`"
    )
    try:
        with httpx.Client(timeout=10) as client:
            client.post(settings.slack_webhook_url, json={"text": text})
    except Exception:
        pass


def _notify_email(*, run_id: str, sector: str, ciudad: str, calientes: int, tibios: int, frios: int) -> None:
    if not settings.resend_api_key:
        return
    total = calientes + tibios + frios
    html = f"""
    <h2>SEÑAL — Pipeline de prospección completado</h2>
    <p><strong>Sector:</strong> {sector} | <strong>Ciudad:</strong> {ciudad}</p>
    <table border="1" cellpadding="6" cellspacing="0">
      <tr><th>Clasificación</th><th>Cantidad</th></tr>
      <tr><td>🟢 Calientes (≥8)</td><td>{calientes}</td></tr>
      <tr><td>🟡 Tibios (6–7.9)</td><td>{tibios}</td></tr>
      <tr><td>⚪ Fríos (3–5.9)</td><td>{frios}</td></tr>
      <tr><td><strong>Total</strong></td><td><strong>{total}</strong></td></tr>
    </table>
    <p>El archivo Excel ya está disponible en el servidor.</p>
    <p><small>Run ID: {run_id}</small></p>
    """
    payload = {
        "from": "SEÑAL Prospección <noreply@prospeccion.kairosdls.com>",
        "to": [settings.resend_to_email] if hasattr(settings, "resend_to_email") and settings.resend_to_email else [],
        "subject": f"[SEÑAL] Pipeline completado — {calientes} leads calientes en {sector}",
        "html": html,
    }
    if not payload["to"]:
        return
    try:
        with httpx.Client(timeout=10) as client:
            client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
    except Exception:
        pass
