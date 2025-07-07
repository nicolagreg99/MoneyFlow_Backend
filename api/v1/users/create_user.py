import psycopg2
import bcrypt
import json
import uuid
from database.connection import connect_to_database, create_cursor
from api.v1.users.send_mail import send_email
from config import APP_BASE_URL

def create_user(username, email, password, first_name, last_name, expenses, incomes):
    if email_exists(email):
        return {"success": False, "message": "Email already exists"}, 400

    if username_exists(username):
        return {"success": False, "message": "Username already exists"}, 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        verification_token = str(uuid.uuid4())

        cursor.execute(
            """
            INSERT INTO users (username, email, password, first_name, last_name, verified, verification_token)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (username, email, hashed_password.decode('utf-8'), first_name, last_name, False, verification_token)
        )
        user_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO user_categories (user_id, expenses_categories, incomes_categories) VALUES (%s, %s, %s)",
            (user_id, json.dumps(expenses), json.dumps(incomes))
        )
        conn.commit()

        verification_link = f"{APP_BASE_URL}/api/v1/verify/{verification_token}"
        email_subject = "Verifica il tuo account"
        email_body = f"""
        <html>
          <body>
            <p>Ciao {first_name},</p>
            <p>Grazie per la registrazione! Per completare l'attivazione del tuo account, clicca sul link qui sotto:</p>
            <p><a href="{verification_link}">Verifica il tuo account</a></p>
            <p>Se non hai richiesto questa registrazione, ignora questa email.</p>
          </body>
        </html>
        """

        result = send_email(email_subject, email_body, email)
        print(f"[CREATE_USER] Risultato invio email: {result}")

        return {
            "success": True,
            "message": "User created successfully. Please check your email to verify your account.",
            "user_id": user_id
        }, 200

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
        return {"success": False, "message": "Database error"}, 500
    finally:
        cursor.close()
        conn.close()


def username_exists(username):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking if username exists: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def email_exists(email):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error checking if email exists: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def verify_user_token(token):
    conn = connect_to_database()
    cursor = create_cursor(conn)
    
    try:
        cursor.execute(
            "SELECT id FROM users WHERE verification_token = %s AND verified = FALSE",
            (token,)
        )
        user = cursor.fetchone()
        
        if user:
            cursor.execute(
                "UPDATE users SET verified = TRUE, verification_token = NULL WHERE id = %s",
                (user[0],)
            )
            conn.commit()
            return True, "Account verificato con successo!"
        else:
            return False, "Token non valido o già usato."
    
    except Exception as e:
        print(f"Errore durante la verifica: {e}")
        return False, "Errore interno al server"
    
    finally:
        cursor.close()
        conn.close()