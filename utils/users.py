from database.connection import connect_to_database, create_cursor

def get_user_currency(user_id):
    conn = connect_to_database()
    cursor = create_cursor(conn)
    try:
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else "EUR"
    finally:
        cursor.close()
        conn.close()
