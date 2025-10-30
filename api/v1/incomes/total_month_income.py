from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
import jwt
from datetime import datetime, timedelta
from utils.currency_converter import currency_converter

def total_incomes_by_month():
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

        # Calcola la data di inizio e fine (ultimi 12 mesi)
        oggi = datetime.today()
        data_inizio = (oggi - timedelta(days=365)).replace(day=1)
        data_fine = (oggi + timedelta(days=31)).replace(day=1)

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        # Query per ottenere la somma delle entrate con valuta
        query = """
            SELECT CAST(EXTRACT(YEAR FROM giorno) AS INTEGER) AS anno,
                   CAST(EXTRACT(MONTH FROM giorno) AS INTEGER) AS mese,
                   SUM(valore) AS totale_per_mese,
                   currency,
                   exchange_rate
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            GROUP BY anno, mese, currency, exchange_rate
            ORDER BY anno, mese;
        """
        cursor.execute(query, (data_inizio, data_fine, user_id))
        totali_mensili = cursor.fetchall()

        # Mappa per ottenere nomi dei mesi
        mesi_nomi = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile", 5: "Maggio", 6: "Giugno",
            7: "Luglio", 8: "Agosto", 9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }

        # Creiamo una struttura per contenere tutti i mesi
        result = {}
        for i in range(12):
            mese_riferimento = (oggi.month - i - 1) % 12 + 1
            anno_riferimento = oggi.year if oggi.month - i > 0 else oggi.year - 1
            result[f"{mesi_nomi[mese_riferimento]} {anno_riferimento}"] = 0.0

        # Calcola totali convertiti per mese
        monthly_totals_converted = {}
        for anno, mese, totale, currency_entrata, exchange_rate in totali_mensili:
            chiave = f"{mesi_nomi[mese]} {anno}"
            totale_val = float(totale or 0)
            exchange_rate_val = float(exchange_rate) if exchange_rate is not None else 1.0
            
            # Conversione valuta
            if currency_entrata == user_currency:
                totale_convertito = totale_val
            else:
                # Usa una data approssimativa del mese per la conversione
                data_riferimento = datetime(anno, mese, 15)
                totale_convertito = currency_converter.convert_amount(
                    totale_val, 
                    data_riferimento,
                    currency_entrata, 
                    user_currency
                )
            
            if chiave in monthly_totals_converted:
                monthly_totals_converted[chiave] += totale_convertito
            else:
                monthly_totals_converted[chiave] = totale_convertito

        # Inseriamo i dati convertiti nei risultati
        for chiave, totale in monthly_totals_converted.items():
            if chiave in result:
                result[chiave] = round(totale, 2)

        return jsonify({
            "currency": user_currency,
            "monthly_totals": result
        }), 200

    except Exception as e:
        print("Errore durante il recupero dei totali mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()