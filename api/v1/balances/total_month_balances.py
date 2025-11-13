from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

def total_balances_by_month(user_id):
    try:
        oggi = datetime.today()
        data_inizio = (oggi - timedelta(days=365)).replace(day=1)
        data_fine = (oggi + timedelta(days=31)).replace(day=1)

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # ✅ Recupera la valuta di default dell’utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        # ✅ Query ENTRATE con conversione in valuta utente
        query_entrate = """
            SELECT 
                CAST(EXTRACT(YEAR FROM giorno) AS INTEGER) AS anno,
                CAST(EXTRACT(MONTH FROM giorno) AS INTEGER) AS mese,
                SUM(
                    valore * 
                    CASE 
                        WHEN exchange_rate IS NOT NULL THEN exchange_rate 
                        ELSE 1 
                    END
                ) AS totale_entrate
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            GROUP BY anno, mese
            ORDER BY anno, mese;
        """
        cursor.execute(query_entrate, (data_inizio, data_fine, user_id))
        totali_entrate = cursor.fetchall()

        # ✅ Query SPESE con conversione in valuta utente
        query_spese = """
            SELECT 
                CAST(EXTRACT(YEAR FROM giorno) AS INTEGER) AS anno,
                CAST(EXTRACT(MONTH FROM giorno) AS INTEGER) AS mese,
                SUM(
                    valore * 
                    CASE 
                        WHEN exchange_rate IS NOT NULL THEN exchange_rate 
                        ELSE 1 
                    END
                ) AS totale_spese
            FROM spese
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            GROUP BY anno, mese
            ORDER BY anno, mese;
        """
        cursor.execute(query_spese, (data_inizio, data_fine, user_id))
        totali_spese = cursor.fetchall()

        # ✅ Mesi in italiano
        mesi_nomi = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile", 5: "Maggio", 6: "Giugno",
            7: "Luglio", 8: "Agosto", 9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }

        # ✅ Genera ultimi 12 mesi
        mesi_list = []
        for i in range(12):
            mese_corrente = (oggi.replace(day=1) - timedelta(days=i * 30))
            chiave = f"{mesi_nomi[mese_corrente.month]} {mese_corrente.year}"
            mesi_list.append(chiave)

        mesi_list = list(dict.fromkeys(mesi_list))  # rimuove duplicati mantenendo l'ordine

        # ✅ Struttura base
        result = {
            mese: {"entrate": 0.00, "spese": 0.00, "valore": 0.00}
            for mese in mesi_list
        }

        # ✅ Inserisci ENTRATE
        for anno, mese, totale_entrate in totali_entrate:
            chiave = f"{mesi_nomi[mese]} {anno}"
            if chiave in result:
                result[chiave]["entrate"] = round(float(totale_entrate or 0), 2)
                result[chiave]["valore"] += result[chiave]["entrate"]

        # ✅ Inserisci SPESE
        for anno, mese, totale_spese in totali_spese:
            chiave = f"{mesi_nomi[mese]} {anno}"
            if chiave in result:
                result[chiave]["spese"] = round(float(totale_spese or 0), 2)
                result[chiave]["valore"] -= result[chiave]["spese"]

        # ✅ Lista finale
        result_list = [
            {
                "mese": mese,
                "entrate": valori["entrate"],
                "spese": valori["spese"],
                "valore": valori["valore"],
                "currency": user_currency
            }
            for mese, valori in result.items()
        ]

        # ✅ Ordinamento opzionale
        sort_by = request.args.get("sort_by")
        order = request.args.get("order", "desc")

        if sort_by == "value_asc":
            result_list.sort(key=lambda x: x["valore"])
        elif sort_by == "value_desc":
            result_list.sort(key=lambda x: x["valore"], reverse=True)
        elif sort_by == "entrate_asc":
            result_list.sort(key=lambda x: x["entrate"])
        elif sort_by == "entrate_desc":
            result_list.sort(key=lambda x: x["entrate"], reverse=True)
        elif sort_by == "spese_asc":
            result_list.sort(key=lambda x: x["spese"])
        elif sort_by == "spese_desc":
            result_list.sort(key=lambda x: x["spese"], reverse=True)
        else:
            if order == "asc":
                result_list = result_list[::-1]

        return jsonify(result_list), 200

    except Exception as e:
        print("❌ Errore durante il recupero dei bilanci mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare i bilanci mensili"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
