from flask import Blueprint, request, jsonify
from api.login.send_mail import send_email
import bcrypt
import psycopg2
import secrets
import datetime
from config import SMTP_USER, SMTP_PASSWORD
from database.connection import connect_to_database, create_cursor

bp = Blueprint('reset_password', __name__)

def generate_reset_token():
    """Genera un token di reset sicuro."""
    return secrets.token_urlsafe(64)

def store_reset_token(username, token):
    """Salva il token di reset nel database."""
    conn = connect_to_database()
    cursor = create_cursor(conn)
    try:
        cursor.execute("UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE username = %s",
                       (token, datetime.datetime.utcnow() + datetime.timedelta(hours=1), username))
        conn.commit()
    except Exception as e:
        print(f"Error storing reset token: {e}")
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
        # Verifica se l'identifier è un'email o un username
        if "@" in identifier:
            cursor.execute("SELECT username, email FROM users WHERE email = %s", (identifier,))
        else:
            cursor.execute("SELECT username, email FROM users WHERE username = %s", (identifier,))
        
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        username, user_email = user

        token = generate_reset_token()
        store_reset_token(username, token)

        reset_link = f"http://192.168.1.93:3000/reset_password?token={token}"
        email_body = f"Click the following link to reset your password: {reset_link}"
        send_email("Password Reset Request", email_body, user_email)

        return jsonify({'success': True, 'message': 'Password reset email sent'}), 200
    
    except Exception as e:
        print(f"Error handling reset request: {e}")
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

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # Controlla se il token esiste e se è ancora valido
        cursor.execute("SELECT username, reset_token_expiry FROM users WHERE reset_token = %s", (token,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid token'}), 400

        # Verifica se il token è scaduto
        token_expiry = user[1]
        if token_expiry < datetime.datetime.utcnow():
            return jsonify({'success': False, 'message': 'Expired token'}), 400

        # Hash della nuova password e decodifica in UTF-8
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"Nuovo hash della password per l'utente {user[0]}: {hashed_password}")

        cursor.execute("UPDATE users SET password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE username = %s",
                       (hashed_password, user[0]))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200

    except Exception as e:
        print(f"Error resetting password: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500
    finally:
        cursor.close()
        conn.close()

