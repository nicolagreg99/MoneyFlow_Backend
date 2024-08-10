from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt

def total_expenses_for_period():
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
        expense_type = request.args.get('tipo')
        
        if not start_date_str or not end_date_str:
            return jsonify({"error": "Start date and end date are required"}), 400

        try:
            start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
        
        query = """
            SELECT SUM(valore)
            FROM spese
            WHERE giorno >= %s AND giorno <= %s AND user_id = %s
        """
        params = [start_date, end_date, user_id]

        if expense_type:
            query += " AND tipo = %s"
            params.append(expense_type)
        
        cursor.execute(query, tuple(params))
        
        total = cursor.fetchone()[0]
        
        if total is None:
            total = 0
        
        return jsonify({"total": total}), 200
    except Exception as e:
        print("Error retrieving totals for the period:", str(e))
        return jsonify({"error": "Unable to retrieve totals for the period"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
