import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_USER, SMTP_PASSWORD
import traceback

def send_email(subject, body, to_email):
    """Invia un'email utilizzando Gmail SMTP con log dettagliato."""
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = SMTP_USER
    smtp_password = SMTP_PASSWORD

    from_email = smtp_user

    print("[SEND_EMAIL] Preparazione invio email")
    print(f"[SEND_EMAIL] From: {from_email}")
    print(f"[SEND_EMAIL] To: {to_email}")
    print(f"[SEND_EMAIL] Subject: {subject}")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        print("[SEND_EMAIL] Connessione al server SMTP...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            print("[SEND_EMAIL] Avvio TLS...")
            server.starttls()

            print("[SEND_EMAIL] Login con credenziali SMTP...")
            server.login(smtp_user, smtp_password)
            print("[SEND_EMAIL] Login riuscito ")

            print("[SEND_EMAIL] Invio email in corso...")
            server.sendmail(from_email, to_email, msg.as_string())
            print("[SEND_EMAIL] Email inviata con successo ")
        return True

    except Exception as e:
        print("[SEND_EMAIL] Errore nell'invio dell'email ")
        traceback.print_exc()
        return False
