from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
from utils.currency_converter import currency_converter

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

        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        tipi = request.args.getlist('tipo')

        query = """
            SELECT tipo, SUM(valore) AS totale_per_tipo, currency, exchange_rate
            FROM entrate
            WHERE giorno BETWEEN %s AND %s
              AND user_id = %s
        """
        params = [from_date, to_date, user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " GROUP BY tipo, currency, exchange_rate;"

        cursor.execute(query, tuple(params))
        totali_per_tipo = cursor.fetchall()
        
        if not totali_per_tipo:
            return jsonify({
                "messaggio": "Nessuna entrata trovata nell'intervallo specificato",
                "currency": user_currency
            }), 200
        
        # Calcola totali convertiti per categoria
        category_totals = {}
        for row in totali_per_tipo:
            tipo = row[0]
            totale = float(row[1] or 0)
            currency_entrata = row[2]
            exchange_rate = float(row[3]) if row[3] is not None else 1.0

            # Conversione valuta
            if currency_entrata == user_currency:
                totale_convertito = totale
            else:
                totale_convertito = currency_converter.convert_amount(
                    totale, 
                    from_date,  # usa la data di inizio intervallo
                    currency_entrata, 
                    user_currency
                )

            if tipo in category_totals:
                category_totals[tipo] += totale_convertito
            else:
                category_totals[tipo] = totale_convertito

        result = [
            {"tipo": tipo, "totale_per_tipo": round(totale, 2)}
            for tipo, totale in category_totals.items()
        ]
        
        return jsonify({
            "currency": user_currency,
            "totali_per_categoria": result
        }), 200

    except Exception as e:
        print("Errore durante il recupero:", str(e))
        return jsonify({"errore": "Errore nel recupero delle entrate"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()