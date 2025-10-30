import json
import datetime
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger

def edit_user(user_id):
    data = request.json
    updated_at = datetime.datetime.utcnow()

    logger.info(f"Starting to update user with ID: {user_id}")
    logger.info(f"Request data: {data}")

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        fields = []
        values = []

        if "first_name" in data:
            fields.append("first_name = %s")
            values.append(data["first_name"])
        if "last_name" in data:
            fields.append("last_name = %s")
            values.append(data["last_name"])
        if "default_currency" in data:
            fields.append("default_currency = %s")
            values.append(data["default_currency"].upper())

        fields.append("updated_at = %s")
        values.append(updated_at)

        if fields:
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            cursor.execute(query, tuple(values))
            logger.info(f"Executed query to update user: {query}")

        cursor.execute("SELECT expenses_categories, incomes_categories FROM user_categories WHERE user_id = %s", (user_id,))
        existing_categories = cursor.fetchone()

        if existing_categories:
            current_expenses = existing_categories[0] or []
            current_incomes = existing_categories[1] or []
        else:
            current_expenses = []
            current_incomes = []

        logger.info(f"Current expenses: {current_expenses}")
        logger.info(f"Current incomes: {current_incomes}")

        new_expenses = data.get("expenses")
        new_incomes = data.get("incomes")

        updated_expenses = new_expenses if new_expenses is not None else current_expenses
        updated_incomes = new_incomes if new_incomes is not None else current_incomes

        if existing_categories:
            update_query = """
                UPDATE user_categories
                SET expenses_categories = %s, incomes_categories = %s
                WHERE user_id = %s
            """
            cursor.execute(update_query, (json.dumps(updated_expenses), json.dumps(updated_incomes), user_id))
            logger.info(f"Executed query to update categories: {update_query}")
        else:
            insert_query = """
                INSERT INTO user_categories (user_id, expenses_categories, incomes_categories)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (user_id, json.dumps(updated_expenses), json.dumps(updated_incomes)))
            logger.info(f"Executed query to insert categories: {insert_query}")

        conn.commit()
        logger.info("Changes committed to the database")

        user_response = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "default_currency": data.get("default_currency", ""),
            "expenses_categories": updated_expenses,
            "incomes_categories": updated_incomes
        }

        logger.info(f"User data after update: {user_response}")

        return jsonify({
            "success": True, 
            "message": "User updated successfully",
            "user": user_response
        }), 200
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating user: {e}")
        return jsonify({"success": False, "message": f"Error updating user: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()