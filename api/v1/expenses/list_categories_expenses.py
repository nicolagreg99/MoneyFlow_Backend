import json
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

def list_categories_expenses(user_id):
    """Restituisce la lista delle categorie di spesa associate a un utente."""
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute(
            "SELECT expenses_categories FROM user_categories WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        if result:
            print(f"DB Result: {result}")  

        expenses_categories = result[0] if result and result[0] else [] 

        return jsonify({"success": True, "categories": expenses_categories}), 200

    except Exception as e:
        print(f"Error fetching expense categories: {e}")  
        return jsonify({"success": False, "message": f"Error fetching categories: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
