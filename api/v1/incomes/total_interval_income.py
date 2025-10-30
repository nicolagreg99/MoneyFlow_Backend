from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
from utils.currency_converter import currency_converter

def total_incomes():
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
        income_types = request.args.getlist('tipo')  

        if not start_date_str or not end_date_str:
            return jsonify({"error": "from_date and to_date are required"}), 400

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format, should be YYYY-MM-DD"}), 400
        
        if end_date < start_date:
            return jsonify({"error": "End date must be after start date"}), 400
        
        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        # Query per entrate con valuta
        query = """
            SELECT valore, currency, exchange_rate, giorno
            FROM entrate
            WHERE giorno BETWEEN %s AND %s AND user_id = %s
        """
        params = [start_date, end_date, user_id]

        if income_types:
            placeholders = ', '.join(['%s'] * len(income_types))
            query += f" AND tipo IN ({placeholders})"
            params.extend(income_types)
        
        cursor.execute(query, tuple(params))
        incomes = cursor.fetchall()

        # Calcola totale convertito
        total = 0
        for income in incomes:
            valore = float(income[0] or 0)
            currency_entrata = income[1]
            exchange_rate = float(income[2]) if income[2] is not None else 1.0
            giorno = income[3]

            # Conversione valuta
            if currency_entrata == user_currency:
                totale_convertito = valore
            else:
                totale_convertito = currency_converter.convert_amount(
                    valore, 
                    giorno,
                    currency_entrata, 
                    user_currency
                )

            total += totale_convertito

        return jsonify({
            "total": round(float(total), 2) if total is not None else 0,
            "currency": user_currency
        }), 200

    except Exception as e:
        print("Error retrieving totals for the period:", str(e))
        return jsonify({"error": "Unable to retrieve totals for the period"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()