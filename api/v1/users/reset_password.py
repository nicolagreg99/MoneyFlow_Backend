from flask import Blueprint, request, jsonify, redirect
from api.v1.users.send_mail import send_email
import bcrypt
import secrets
import datetime
import logging
import re

from database.connection import connect_to_database, create_cursor
from config import APP_BASE_URL   # ⬅️ USIAMO CONFIG.PY

# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

bp = Blueprint('reset_password', __name__)

# =========================
# UTILS
# =========================
def generate_reset_token():
    """Genera un token di reset sicuro."""
    return secrets.token_urlsafe(64)

def is_strong_password(password):
    """Almeno 8 caratteri, un numero e una lettera maiuscola."""
    return (
        len(password) >= 8
        and bool(re.search(r"\d", password))
        and bool(re.search(r"[A-Z]", password))
    )

def store_reset_token(username, token):
    conn = connect_to_database()
    cursor = create_cursor(conn)
    try:
        cursor.execute(
            """
            UPDATE users
            SET reset_token = %s,
                reset_token_expiry = %s
            WHERE username = %s
            """,
            (token, datetime.datetime.utcnow() + datetime.timedelta(hours=1), username)
        )
        conn.commit()
    except Exception as e:
        logging.error(f"Error storing reset token: {e}")
    finally:
        cursor.close()
        conn.close()

# =========================
# REQUEST RESET (EMAIL)
# =========================
@bp.route('/request_reset', methods=['POST'])
def request_reset():
    data = request.json
    identifier = data.get('identifier')

    if not identifier:
        return jsonify({'success': False, 'message': 'Username or email required'}), 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        if "@" in identifier:
            cursor.execute(
                """
                SELECT username, email, reset_token, reset_token_expiry
                FROM users
                WHERE LOWER(email) = LOWER(%s)
                """,
                (identifier,)
            )
        else:
            cursor.execute(
                """
                SELECT username, email, reset_token, reset_token_expiry
                FROM users
                WHERE username = %s
                """,
                (identifier,)
            )

        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        username, user_email, existing_token, token_expiry = user

        if existing_token and token_expiry and token_expiry > datetime.datetime.utcnow():
            token = existing_token
        else:
            token = generate_reset_token()
            store_reset_token(username, token)

        # 🔗 LINK HTTP (email-safe)
        reset_link = f"{APP_BASE_URL}/reset?token={token}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 20px;">
            <table style="max-width:600px;margin:auto;background:#fff;border-radius:8px;">
                <tr>
                    <td style="background:#007bff;color:#fff;padding:20px;text-align:center;font-size:24px;">
                        Reimposta la tua password
                    </td>
                </tr>
                <tr>
                    <td style="padding:20px;color:#333;">
                        <p>Gentile {username},</p>
                        <p>Hai richiesto di reimpostare la tua password.</p>
                        <p style="text-align:center;">
                            <a href="{reset_link}"
                               style="background:#28a745;color:#fff;padding:12px 24px;
                                      text-decoration:none;border-radius:5px;font-size:16px;">
                                Reimposta Password
                            </a>
                        </p>
                        <p>Se il pulsante non funziona, copia e incolla questo link:</p>
                        <p style="word-break:break-word;">
                            <a href="{reset_link}">{reset_link}</a>
                        </p>
                        <p>Se non hai richiesto questa operazione, ignora questa email.</p>
                        <p>Grazie,<br>Money App</p>
                    </td>
                </tr>
                <tr>
                    <td style="background:#f1f1f1;padding:10px;text-align:center;font-size:12px;">
                        © {datetime.datetime.utcnow().year} Money App
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        send_email(
            "Richiesta di Reimpostazione della Password",
            html_body,
            user_email
        )

        return jsonify({'success': True, 'message': 'Password reset email sent'}), 200

    except Exception as e:
        logging.error(f"Error handling reset request: {e}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500
    finally:
        cursor.close()
        conn.close()

# =========================
# HTTP → DEEP LINK
# =========================
@bp.route('/reset', methods=['GET'])
def reset_redirect():
    token = request.args.get('token')
    if not token:
        return "Token mancante", 400

    return redirect(f"moneyapp://reset_password?token={token}")

# =========================
# RESET PASSWORD (API)
# =========================
@bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('password')

    if not token or not new_password:
        return jsonify({'success': False, 'message': 'Token and new password required'}), 400

    if not is_strong_password(new_password):
        return jsonify({
            'success': False,
            'message': 'Password must be at least 8 characters, with a number and an uppercase letter'
        }), 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute(
            "SELECT username, reset_token_expiry FROM users WHERE reset_token = %s",
            (token,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid token'}), 400

        if user[1] < datetime.datetime.utcnow():
            return jsonify({'success': False, 'message': 'Expired token'}), 400

        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute(
            """
            UPDATE users
            SET password = %s,
                reset_token = NULL,
                reset_token_expiry = NULL,
                last_password_change = NOW()
            WHERE username = %s
            """,
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
