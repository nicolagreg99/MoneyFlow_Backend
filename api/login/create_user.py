import psycopg2
import bcrypt
from database.connection import connect_to_database, create_cursor
from config import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST

conn = connect_to_database()
cursor = create_cursor(conn)

def create_user(username, email, password):
    if email_exists(email):
        return {"success": False, "message": "Email already exists"}, 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id", 
            (username, email, hashed_password.decode('utf-8'))
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return {"success": True, "message": "User created successfully", "user_id": user_id}, 200
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return {"success": False, "message": "Error creating user"}, 500
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
