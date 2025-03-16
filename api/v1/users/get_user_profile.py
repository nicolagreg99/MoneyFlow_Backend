import logging
from flask import jsonify
from database.connection import connect_to_database, create_cursor

logger = logging.getLogger(__name__)

def get_user_profile(user_id):
    """Restituisce il profilo dell'utente autenticato, incluse le preferenze."""
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        logger.info(f"Fetching user profile for user_id: {user_id}")

        # Query aggiornata per includere le categorie
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, 
                   uc.expenses_categories, uc.incomes_categories
            FROM users u
            LEFT JOIN user_categories uc ON u.id = uc.user_id
            WHERE u.id = %s
        """, (user_id,))
        
        user = cursor.fetchone()

        if user:
            user_info = {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4],
                "expenses_categories": user[5] if user[5] else [],
                "incomes_categories": user[6] if user[6] else []
            }
            logger.info(f"User profile data: {user_info}")
            return jsonify(user_info), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        return jsonify({"message": f"Error retrieving user profile: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()
