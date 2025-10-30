from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
from utils.currency_converter import currency_converter

def incomes_list(user_id):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        tipi = request.args.getlist('tipo') 

        if not from_date_str or not to_date_str:
            return jsonify({"error": "from_date e to_date sono richiesti"}), 400

        try:
            data_inizio = datetime.strptime(from_date_str, '%Y-%m-%d')
            data_fine = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato delle date non valido. Usa YYYY-MM-DD."}), 400

        if data_fine < data_inizio:
            return jsonify({"error": "La data di fine deve essere successiva alla data di inizio"}), 400

        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        query = """
            SELECT 
                id, valore, tipo, giorno, inserted_at, user_id, 
                currency, exchange_rate, fields ->> 'descrizione' AS descrizione
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
        """
        params = [data_inizio, data_fine + timedelta(days=1), user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " ORDER BY giorno DESC"

        cursor.execute(query, tuple(params))
        entrate_mensili = cursor.fetchall()

        if not entrate_mensili:
            return jsonify({
                "messaggio": "Nessuna entrata registrata nel periodo specificato",
                "default_currency": user_currency
            }), 200

        entrate_json = []
        for entrata in entrate_mensili:
            valore_originale = float(entrata[1])
            currency_entrata = entrata[6]
            exchange_rate = float(entrata[7]) if entrata[7] is not None else 1.0
            
            # Conversione valuta
            if currency_entrata == user_currency:
                valore_convertito = valore_originale
            else:
                valore_convertito = currency_converter.convert_amount(
                    valore_originale, 
                    entrata[3],  # giorno
                    currency_entrata, 
                    user_currency
                )

            entrate_json.append({
                "id": entrata[0],
                "valore": valore_originale,
                "converted_value": valore_convertito,
                "tipo": entrata[2],
                "giorno": entrata[3].strftime('%Y-%m-%d'),
                "inserted_at": entrata[4].strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": entrata[5],
                "currency": currency_entrata,
                "exchange_rate": exchange_rate,
                "descrizione": entrata[8] if entrata[8] else "",
                "user_currency": user_currency
            })

        return jsonify({
            "default_currency": user_currency,
            "incomes": entrate_json
        }), 200

    except Exception as e:
        print("Errore durante il recupero delle entrate mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare le entrate mensili"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()