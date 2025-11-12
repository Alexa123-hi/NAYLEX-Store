# -*- coding: utf-8 -*-
# email_sender.py – Integración con Brevo (solo para recuperación de contraseña)

import os
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

# ----------------------------
# VARIABLES DE ENTORNO
# ----------------------------
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_SENDER = os.environ.get("BREVO_SENDER", "NAYLEX Store <no-reply@naylexstore.com>")

# ----------------------------
# CONFIGURACIÓN DEL CLIENTE
# ----------------------------
config = Configuration()
if BREVO_API_KEY:
    config.api_key["api-key"] = BREVO_API_KEY
else:
    print("⚠️ Advertencia: Falta configurar la variable de entorno BREVO_API_KEY.")

# ----------------------------
# FUNCIÓN DE ENVÍO
# ----------------------------
def enviar_correo(destinatario: str, asunto: str, html: str, texto: str = None) -> bool:
    """Envía un correo transaccional usando la API de Brevo."""
    api_instance = TransactionalEmailsApi(ApiClient(config))

    # Separar nombre y correo del remitente
    if "<" in BREVO_SENDER and ">" in BREVO_SENDER:
        nombre = BREVO_SENDER.split("<")[0].strip()
        correo = BREVO_SENDER.split("<")[1].replace(">", "").strip()
    else:
        nombre, correo = "NAYLEX Store", BREVO_SENDER

    send_email = SendSmtpEmail(
        to=[{"email": destinatario}],
        sender={"name": nombre, "email": correo},
        subject=asunto,
        html_content=html,
        text_content=texto or "Restablece tu contraseña en NAYLEX Store."
    )

    try:
        response = api_instance.send_transac_email(send_email)
        print(f"✅ Correo enviado correctamente a {destinatario}")
        print("📬 Respuesta Brevo:", response)
        return True
    except ApiException as e:
        print("❌ Error al enviar correo con Brevo:", e)
        return False
    except Exception as ex:
        print("⚠️ Excepción inesperada:", ex)
        return False
