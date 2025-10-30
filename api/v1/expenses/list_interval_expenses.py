from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
from utils.currency_converter import currency_converter

def expenses_list(user_id):
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

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        query = """
            SELECT 
                id,
                valore,
                tipo,
                giorno,
                inserted_at,
                user_id,
                currency,
                exchange_rate,
                fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s 
              AND giorno < %s 
              AND user_id = %s
              AND valore IS NOT NULL
        """
        params = [data_inizio, data_fine + timedelta(days=1), user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " ORDER BY giorno DESC"

        cursor.execute(query, tuple(params))
        spese_mensili = cursor.fetchall()

        if not spese_mensili:
            return jsonify({
                "messaggio": "Nessuna spesa trovata nel periodo specificato",
                "default_currency": user_currency
            }), 200

        spese_json = []
        for spesa in spese_mensili:
            if spesa[1] is not None:
                valore_originale = float(spesa[1])
                currency_spesa = spesa[6]
                exchange_rate = float(spesa[7]) if spesa[7] is not None else 1.0
                
                # DEBUG
                print(f"DEBUG: Convertendo {valore_originale} {currency_spesa} -> {user_currency}")
                print(f"DEBUG: Giorno: {spesa[3]}")
                
                if currency_spesa == user_currency:
                    valore_convertito = valore_originale
                else:
                    valore_convertito = currency_converter.convert_amount(
                        valore_originale,
                        spesa[3],
                        currency_spesa, 
                        user_currency
                    )
                
                print(f"DEBUG: Risultato: {valore_convertito}")

                spese_json.append({
                    "id": spesa[0],
                    "valore": valore_originale,
                    "converted_value": valore_convertito,
                    "tipo": spesa[2],
                    "giorno": spesa[3].strftime('%Y-%m-%d') if spesa[3] else None,
                    "inserted_at": spesa[4].strftime('%Y-%m-%d %H:%M:%S') if spesa[4] else None,
                    "user_id": spesa[5],
                    "currency": currency_spesa,
                    "exchange_rate": exchange_rate,
                    "descrizione": spesa[8] if spesa[8] else "",
                    "user_currency": user_currency
                })

        return jsonify({
            "default_currency": user_currency,
            "expenses": spese_json
        }), 200

    except Exception as e:
        print("Errore durante il recupero delle spese:", str(e))
        return jsonify({
            "errore": "Impossibile recuperare le spese",
            "dettaglio": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()