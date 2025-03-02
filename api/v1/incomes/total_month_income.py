from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
import jwt
from datetime import datetime, timedelta

def total_incomes_by_month():
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
        data_inizio = (oggi - timedelta(days=365)).replace(day=1)  # 1° giorno di 12 mesi fa
        data_fine = (oggi + timedelta(days=31)).replace(day=1)  # 1° giorno del mese successivo

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Query per ottenere la somma delle entrate negli ultimi 12 mesi
        query = """
            SELECT CAST(EXTRACT(YEAR FROM giorno) AS INTEGER) AS anno,
                   CAST(EXTRACT(MONTH FROM giorno) AS INTEGER) AS mese,
                   SUM(valore) AS totale_per_mese
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            GROUP BY anno, mese
            ORDER BY anno, mese;
        """
        cursor.execute(query, (data_inizio, data_fine, user_id))
        totali_mensili = cursor.fetchall()

        # Mappa per ottenere nomi dei mesi
        mesi_nomi = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile", 5: "Maggio", 6: "Giugno",
            7: "Luglio", 8: "Agosto", 9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }

        # Creiamo una struttura per contenere tutti i mesi, anche se alcuni hanno valore 0
        result = {}
        for i in range(12):
            mese_riferimento = (oggi.month - i - 1) % 12 + 1  # Calcola il mese corretto
            anno_riferimento = oggi.year if oggi.month - i > 0 else oggi.year - 1  # Calcola l'anno corretto
            result[f"{mesi_nomi[mese_riferimento]} {anno_riferimento}"] = 0  # Default a 0

        # Inseriamo i dati dalla query nei risultati
        for anno, mese, totale in totali_mensili:
            chiave = f"{mesi_nomi[mese]} {anno}"
            result[chiave] = round(float(totale), 2)  # Assicuriamo il formato corretto

        return jsonify(result), 200

    except Exception as e:
        print("Errore durante il recupero dei totali mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili"}), 500
