import json
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

def list_categories_expenses(user_id):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("""
            SELECT 
                uc.expenses_categories,
                u.default_currency
            FROM user_categories uc
            JOIN users u ON uc.user_id = u.id
            WHERE uc.user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()

        if not result:
            return jsonify({"success": False, "message": "User not found"}), 404

        expenses_categories = result[0] if result[0] else []
        default_currency = result[1] if result[1] else "EUR"

        return jsonify({
            "success": True,
            "categories": expenses_categories,
            "default_currency": default_currency
        }), 200

    except Exception as e:
        print(f"Error fetching expense categories: {e}")
        return jsonify({
            "success": False,
            "message": f"Error fetching categories: {str(e)}"
        }), 500

    finally:
        cursor.close()
        conn.close()