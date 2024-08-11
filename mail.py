import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_email(subject, body, to_email):
    """Invia un'email utilizzando Gmail SMTP."""
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = os.getenv('SMTP_USER')  # La tua email Gmail
    smtp_password = os.getenv('SMTP_PASSWORD')  # La password per le app generata

    from_email = smtp_user

    # Crea il messaggio
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Aggiungi il corpo del messaggio
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connessione al server SMTP di Gmail
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Sicurezza della connessione
            server.login(smtp_user, smtp_password)  # Login
            server.sendmail(from_email, to_email, msg.as_string())  # Invio email
        print("Email inviata con successo.")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

# Esempio di utilizzo
subject = 'Test Email'
body = 'O VENADA. Questa è una email di test inviata tramite Gmail SMTP. '
to_email = 'zvenada@gmail.com'  # Modifica con l'email del destinatario
send_email(subject, body, to_email)
