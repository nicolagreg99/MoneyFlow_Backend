from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
import logging

logger = logging.getLogger(__name__)

def total_expenses(base_currency="EUR"):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded_token = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if not user_id:
            return jsonify({"error": "User ID is missing from token"}), 401

        start_date_str = request.args.get('from_date')
        end_date_str = request.args.get('to_date')
        expense_types = request.args.getlist('tipo')

        if not start_date_str or not end_date_str:
            return jsonify({"error": "from_date and to_date are required"}), 400

        try:
            start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

        query = """
            SELECT SUM(valore_base)
            FROM spese
            WHERE giorno BETWEEN %s AND %s
              AND user_id = %s
        """
        params = [start_date, end_date, user_id]

        if expense_types:
            placeholders = ', '.join(['%s'] * len(expense_types))
            query += f" AND tipo IN ({placeholders})"
            params.extend(expense_types)

        cursor.execute(query, tuple(params))
        total = cursor.fetchone()[0] or 0

        logger.info(f"Total expenses calculated for user_id={user_id}, range={start_date_str} - {end_date_str}, total={total}")

        return jsonify({
            "total": round(float(total), 2),
            "currency": base_currency
        }), 200

    except Exception as e:
        logger.error(f"Error while calculating total expenses: {e}")
        return jsonify({"error": "Unable to calculate total expenses"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
