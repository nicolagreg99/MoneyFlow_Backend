import json
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

def list_categories_incomes(user_id):
    """Restituisce la lista delle categorie di entrate associate a un utente."""
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute(
            "SELECT incomes_categories FROM user_categories WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        if result:
            print(f"DB Result: {result}")  

        incomes_categories = result[0] if result and result[0] else [] 

        return jsonify({"success": True, "categories": incomes_categories}), 200

    except Exception as e:
        print(f"Error fetching income categories: {e}")  
        return jsonify({"success": False, "message": f"Error fetching categories: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
