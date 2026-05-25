"""
Prueba rápida de Resend. Ejecutar desde la raíz del backend:
  python test_resend.py
"""

import httpx

RESEND_API_KEY = "re_6JGPAVhH_5Xe8WpjPCMW7urQZ1m5pWn3J"
RESEND_TO_EMAIL = "gerencia@kairosdls.com"

# Resend permite este remitente sin verificar dominio (plan gratuito / pruebas)
FROM_ADDRESS = "SEÑAL Prospección <noreply@prospeccion.kairosdls.com>"

payload = {
    "from": FROM_ADDRESS,
    "to": [RESEND_TO_EMAIL],
    "subject": "[SEÑAL] Prueba de notificación — correo de test",
    "html": """
    <h2 style="color:#0369A1;">SEÑAL — Notificaciones activas</h2>
    <p>Este es un correo de prueba para verificar que las notificaciones del pipeline funcionan correctamente.</p>
    <hr/>
    <p>Cuando una ejecución de prospección termine, recibirás un resumen como este:</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
      <tr style="background:#0F172A;color:white;">
        <th>Clasificación</th><th>Cantidad</th>
      </tr>
      <tr><td>✅ Calientes (score ≥8)</td><td>5</td></tr>
      <tr><td>🟡 Tibios (score 6–7.9)</td><td>8</td></tr>
      <tr><td>⚪ Fríos (score 3–5.9)</td><td>12</td></tr>
      <tr style="font-weight:bold;"><td>Total</td><td>25</td></tr>
    </table>
    <p style="color:#666;font-size:12px;">Kairos DLS Group S.A.S. — SEÑAL</p>
    """,
}

print(f"Enviando correo de prueba a {RESEND_TO_EMAIL}...")

with httpx.Client(timeout=15) as client:
    resp = client.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json=payload,
    )

if resp.status_code in (200, 201):
    data = resp.json()
    print(f"✅ Correo enviado exitosamente. ID: {data.get('id')}")
    print()
    print("IMPORTANTE: El remitente actual es 'onboarding@resend.dev' (dominio de prueba).")
    print("Para producción, verifica 'kairosdls.com' en app.resend.com/domains")
    print("y cambia FROM_ADDRESS a 'noreply@kairosdls.com'.")
else:
    print(f"❌ Error {resp.status_code}: {resp.text}")
    if resp.status_code == 403:
        print()
        print("Posible causa: el dominio del remitente no está verificado en Resend.")
        print("Solución: verifica 'kairosdls.com' en app.resend.com/domains")
        print("O usa 'onboarding@resend.dev' como remitente para pruebas.")
