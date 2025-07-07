import psycopg2
import json
import bcrypt
from database.connection import connect_to_database, create_cursor
from config import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST

def authenticate_user(username, password):
    conn = connect_to_database()
    cursor = create_cursor(conn)
    
    try:
        # Recupera anche il flag verified
        cursor.execute(
            "SELECT id, username, password, email, verified FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            # Controlla se l'utente è verificato
            if not user[4]:
                print("Utente non verificato.")
                return {"error": "Account non verificato. Controlla la tua email per attivarlo."}
            
            # Verifica la password
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                cursor.execute(
                    "UPDATE users SET last_access = CURRENT_TIMESTAMP WHERE username = %s",
                    (username,)
                )
                conn.commit()
                
                user_data = {
                    "id": user[0],
                    "username": user[1],
                    "email": user[3]
                }
                return user_data
            else:
                print("La password non corrisponde.")
                return None
        else:
            print("Utente non trovato.")
            return None
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
