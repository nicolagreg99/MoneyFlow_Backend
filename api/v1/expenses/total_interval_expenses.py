from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt

def total_expenses():
    conn = None
    cursor = None
    
    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Recupero token
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # Decodifica token JWT
        try:
            decoded_token = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if not user_id:
            return jsonify({"error": "User ID is missing from token"}), 401

        # Recupero parametri GET
        start_date_str = request.args.get('from_date')
        end_date_str = request.args.get('to_date')
        expense_types = request.args.getlist('tipo')  # Ottiene una lista di parametri 'tipo'
        
        if not start_date_str or not end_date_str:
            return jsonify({"error": "Start date and end date are required"}), 400

        # Parsing delle date
        try:
            start_date = datetime.strptime(start_date_str.split('T')[0], '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str.split('T')[0], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
        
        # Costruzione query SQL dinamica
        query = """
            SELECT SUM(valore)
            FROM spese
            WHERE giorno >= %s AND giorno <= %s AND user_id = %s
        """
        params = [start_date, end_date, user_id]

        # Se sono stati forniti più tipi di spesa
        if expense_types:
            placeholders = ', '.join(['%s'] * len(expense_types))  # Genera segnaposti dinamici
            query += f" AND tipo IN ({placeholders})"
            params.extend(expense_types)  # Aggiunge i tipi di spesa ai parametri
        
        cursor.execute(query, tuple(params))
        
        # Recupero risultato
        total = cursor.fetchone()[0] or 0
        
        return jsonify({"total": total}), 200

    except Exception as e:
        print("Error retrieving totals for the period:", str(e))
        return jsonify({"error": "Unable to retrieve totals for the period"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
