from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
from utils.currency_converter import currency_converter

def total_incomes_by_day():
    conn = None
    cursor = None
    
    try:
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

        mese = request.args.get('mese')
        anno = request.args.get('anno')

        if not mese or not anno:
            return jsonify({"error": "Month and Year are required"}), 400

        try:
            mese = int(mese)
            anno = int(anno)
            start_date = datetime(anno, mese, 1)
            end_date = (start_date.replace(month=mese + 1) if mese < 12 else start_date.replace(year=anno + 1, month=1))
        except ValueError:
            return jsonify({"error": "Invalid Month or Year"}), 400

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        # Query per totali giornalieri con valuta
        query = """
            SELECT giorno, SUM(valore) AS totale_per_giorno, currency, exchange_rate
            FROM entrate
            WHERE giorno >= %s AND giorno < %s
              AND user_id = %s
            GROUP BY giorno, currency, exchange_rate
            ORDER BY giorno;
        """
        cursor.execute(query, (start_date, end_date, user_id))

        totali_giornalieri = cursor.fetchall()

        if not totali_giornalieri:
            return jsonify({"messaggio": "Nessuna entrata nel mese e anno specificati"}), 200

        # Calcola totali convertiti
        daily_totals_converted = {}
        for row in totali_giornalieri:
            giorno = row[0]
            totale = float(row[1] or 0)
            currency_entrata = row[2]
            exchange_rate = float(row[3]) if row[3] is not None else 1.0

            # Conversione valuta
            if currency_entrata == user_currency:
                totale_convertito = totale
            else:
                totale_convertito = currency_converter.convert_amount(
                    totale, 
                    giorno,
                    currency_entrata, 
                    user_currency
                )

            if giorno in daily_totals_converted:
                daily_totals_converted[giorno] += totale_convertito
            else:
                daily_totals_converted[giorno] = totale_convertito

        # Prepara la risposta JSON
        result = [
            {
                "giorno": giorno.day, 
                "totale_per_giorno": round(totale, 2),
                "currency": user_currency
            }
            for giorno, totale in daily_totals_converted.items()
        ]

        return jsonify(result), 200

    except Exception as e:
        print("Errore durante il recupero dei totali giornalieri:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali giornalieri"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()