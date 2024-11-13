from email.message import EmailMessage
import smtplib
import random
import string

def enviar_mensaje(email, codigo, message=None, subject=None):
    sender_email = "intellihome.playitaiguana@gmail.com"
    sender_password = "feum sttx vaqc peip"

    msg = EmailMessage()
    msg_content = ""
    if not message:
        msg_content = f"""
    Estimado usuario,

    Saludos desde Intelli Home. A continuación, le proporcionamos su código de verificación:

    Código de verificación: {codigo}

    Por favor, ingrese este código en la página de verificación para completar su registro.

    ¡Gracias por confiar en nosotros!

    Atentamente,
    El equipo de Intelli Home.
        """
    else:
        msg_content = message

    msg.set_content(msg_content)

    if subject:
        msg["Subject"] = subject
    else:
        msg["Subject"] = "Código de Verificación"
        
    msg["From"] = sender_email
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

def generar_codigo_verificacion():
    return ''.join(random.choices(string.digits, k=6))
