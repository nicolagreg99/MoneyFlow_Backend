import json
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

import json
import datetime
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

def edit_user(user_id):
    """Modifica nome, cognome e categorie di spesa/entrata per un utente autenticato."""
    data = request.json
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    expenses = data.get("expenses", [])
    incomes = data.get("incomes", [])
    updated_at = datetime.datetime.utcnow()

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute(
            "UPDATE users SET first_name = %s, last_name = %s, updated_at = %s WHERE id = %s",
            (first_name, last_name, updated_at, user_id),
        )

        cursor.execute(
            "UPDATE user_categories SET expenses_categories = %s, incomes_categories = %s WHERE user_id = %s",
            (json.dumps(expenses), json.dumps(incomes), user_id)
        )

        conn.commit()
        return jsonify({"success": True, "message": "User updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Error updating user: {e}")
        return jsonify({"success": False, "message": "Error updating user"}), 500
    finally:
        cursor.close()
        conn.close()
