from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt

def total_incomes_by_category():
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

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')

        if not from_date_str or not to_date_str:
            return jsonify({"error": "Start date and end date are required"}), 400
        
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400

        if to_date < from_date:
            return jsonify({"error": "End date must be after start date"}), 400

        tipi = request.args.getlist('tipo')  # Supporta più valori "tipo"

        query = """
            SELECT tipo, SUM(valore) AS totale_per_tipo
            FROM entrate
            WHERE giorno BETWEEN %s AND %s
              AND user_id = %s
        """
        params = [from_date, to_date, user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " GROUP BY tipo;"

        cursor.execute(query, tuple(params))
        totali_per_tipo = cursor.fetchall()
        
        if not totali_per_tipo:
            return jsonify({"messaggio": "Nessuna entrata trovata nell'intervallo specificato"}), 200
        
        result = [{"tipo": row[0], "totale_per_tipo": row[1]} for row in totali_per_tipo]
        
        return jsonify(result), 200

    except Exception as e:
        print("Errore durante il recupero:", str(e))
        return jsonify({"errore": "Errore nel recupero delle entrate"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
