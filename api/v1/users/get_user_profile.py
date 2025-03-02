import logging
from flask import jsonify
from database.connection import connect_to_database, create_cursor

logger = logging.getLogger(__name__)

def get_user_profile(current_user_id):
    """Restituisce il profilo dell'utente autenticato."""
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        logger.info(f"Fetching user profile for user_id: {current_user_id}")
        cursor.execute("SELECT id, username, email, first_name, last_name FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()

        if user:
            user_info = {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4]
            }
            logger.info(f"User profile data: {user_info}")
            return jsonify(user_info), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        return jsonify({"message": "Error retrieving user profile"}), 500

    finally:
        cursor.close()
        conn.close()
