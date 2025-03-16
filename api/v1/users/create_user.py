import psycopg2
import bcrypt
import json
from database.connection import connect_to_database, create_cursor
from config import DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, DATABASE_HOST

conn = connect_to_database()
cursor = create_cursor(conn)

def create_user(username, email, password, first_name, last_name, expenses, incomes):
    if email_exists(email):
        return {"success": False, "message": "Email already exists"}, 400

    if username_exists(username):
        return {"success": False, "message": "Username already exists"}, 400

    conn = connect_to_database()
    cursor = create_cursor(conn)

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, first_name, last_name) VALUES (%s, %s, %s, %s, %s) RETURNING id", 
            (username, email, hashed_password.decode('utf-8'), first_name, last_name)
        )
        user_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO user_categories (user_id, expenses_categories, incomes_categories) VALUES (%s, %s, %s)",
            (user_id, json.dumps(expenses), json.dumps(incomes))
        )

        conn.commit()
        return {"success": True, "message": "User created successfully", "user_id": user_id}, 200
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
