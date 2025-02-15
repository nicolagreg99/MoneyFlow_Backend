from flask import Blueprint, request, jsonify
from api.login.send_mail import send_email
import bcrypt
import psycopg2
import secrets
import datetime
import logging
import re
from database.connection import connect_to_database, create_cursor

# Configura logging
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

bp = Blueprint('reset_password', __name__)

def generate_reset_token():
    """Genera un token di reset sicuro."""
    return secrets.token_urlsafe(64)

def is_strong_password(password):
    """Verifica che la password sia forte: almeno 8 caratteri, un numero e una lettera maiuscola."""
    return len(password) >= 8 and bool(re.search(r"\d", password)) and bool(re.search(r"[A-Z]", password))

def store_reset_token(username, token):
    """Salva il token di reset nel database."""
    conn = connect_to_database()
    cursor = create_cursor(conn)
    try:
        cursor.execute(
            "UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE username = %s",
            (token, datetime.datetime.utcnow() + datetime.timedelta(hours=1), username)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing reset token: {e}")
    finally:
        cursor.close()
        conn.close()

@bp.route('/request_reset', methods=['POST'])
def request_reset():
    data = request.json
    identifier = data.get('identifier')  # Può essere sia username che email

    if not identifier:
        return jsonify({'success': False, 'message': 'Username or email required'}), 400

    conn = connect_to_database()
    cursor = create_cursor(conn)
    
    try:
        # Verifica se è email o username e usa LOWER() per evitare problemi di maiuscole/minuscole
        if "@" in identifier:
            cursor.execute("SELECT username, email, reset_token, reset_token_expiry FROM users WHERE LOWER(email) = LOWER(%s)", (identifier,))
        else:
            cursor.execute("SELECT username, email, reset_token, reset_token_expiry FROM users WHERE username = %s", (identifier,))
        
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        username, user_email, existing_token, token_expiry = user

        # Se esiste già un token valido, lo riutilizziamo
        if existing_token and token_expiry and token_expiry > datetime.datetime.utcnow():
            token = existing_token
        else:
            token = generate_reset_token()
            store_reset_token(username, token)

        # Deep link per il reset password
        reset_link = f"moneyapp://reset_password?token={token}"

        # HTML dell'email con deep link nel pulsante e nel testo
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f7f7f7; padding: 20px;">
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                <tr>
                    <td style="padding: 20px; text-align: center; background-color: #007bff; color: #ffffff; font-size: 24px; font-weight: bold;">
                        Reimposta la tua password
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px;">
                        <p>Gentile {username},</p>
                        <p>Hai richiesto di reimpostare la tua password. Clicca sul pulsante qui sotto per procedere:</p>
                        <p style="text-align: center;">
                            <!-- Deep link nel pulsante -->
                            <a href="moneyapp://reset_password?token={token}" style="display: inline-block; background-color: #28a745; color: white; padding: 12px 24px; text-align: center; text-decoration: none; font-size: 16px; border-radius: 5px;">
                                Reimposta Password
                            </a>
                        </p>
                        <p>Se il pulsante non funziona, copia e incolla il seguente link nel tuo browser:</p>
                        <p style="word-break: break-word;">
                            <!-- Deep link nel testo -->
                            <a href="moneyapp://reset_password?token={token}" style="color: #007bff; text-decoration: none;">moneyapp://reset_password?token={token}</a>
                        </p>
                        <p>Se non hai richiesto questa operazione, puoi ignorare questa email.</p>
                        <p>Grazie,<br>Il Team di Supporto</p>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px; text-align: center; background-color: #f1f1f1; color: #555; font-size: 12px;">
                        © 2024 Money-app. Tutti i diritti riservati.
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """


        send_email("Richiesta di Reimpostazione della Password", html_body, user_email)

        return jsonify({'success': True, 'message': 'Password reset email sent'}), 200
    
    except Exception as e:
        logging.error(f"Error handling reset request: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500
    finally:
        cursor.close()
        conn.close()

@bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({'success': False, 'message': 'Token and new password required'}), 400

    if not is_strong_password(new_password):
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long, with a number and an uppercase letter'}), 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("SELECT username, reset_token_expiry FROM users WHERE reset_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid token'}), 400

        token_expiry = user[1]
        if token_expiry < datetime.datetime.utcnow():
            return jsonify({'success': False, 'message': 'Expired token'}), 400

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute(
            "UPDATE users SET password = %s, reset_token = NULL, reset_token_expiry = NULL, last_password_change = NOW() WHERE username = %s",
            (hashed_password, user[0])
        )
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200

    except Exception as e:
        logging.error(f"Error resetting password: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500
    finally:
        cursor.close()
        conn.close()
