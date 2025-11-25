from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def total_balances_by_month(user_id):
    try:
        print("=== total_balances_by_month START ===")
        oggi = datetime.today()
        print("oggi:", oggi)

        data_inizio = (oggi - timedelta(days=365)).replace(day=1)
        data_fine = (oggi + timedelta(days=31)).replace(day=1)

        print("data_inizio:", data_inizio)
        print("data_fine:", data_fine)

        conn = connect_to_database()
        cursor = create_cursor(conn)

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"
        print("user_currency:", user_currency)

        print("Eseguo query entrate...")
        cursor.execute("""
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
        """, (data_inizio, data_fine, user_id))

        totali_entrate = cursor.fetchall()
        print("totali_entrate:", totali_entrate)

        print("Eseguo query spese...")
        cursor.execute("""
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
        """, (data_inizio, data_fine, user_id))

        totali_spese = cursor.fetchall()
        print("totali_spese:", totali_spese)

        # === GENERA TUTTI I MESI YYYY-MM ===
        mesi_list = []
        start_month = oggi.replace(day=1)

        print("Generazione mesi YYYY-MM...")
        for i in range(12):
            mese_corrente = start_month - relativedelta(months=i)
            key = f"{mese_corrente.year}-{mese_corrente.month:02d}"
            print("Aggiungo mese:", key)
            mesi_list.append(key)

        # ORDINA I MESI in ordine cronologico
        mesi_list = sorted(mesi_list)
        print("mesi_list ordinata:", mesi_list)

        result = {key: {"entrate": 0.00, "spese": 0.00, "valore": 0.00} for key in mesi_list}

        print("Popolo entrate/spese...")

        for anno, mese, totale_entrate in totali_entrate:
            key = f"{anno}-{mese:02d}"
            print("entrate:", key, totale_entrate)
            if key in result:
                result[key]["entrate"] = float(totale_entrate or 0)
                result[key]["valore"] += result[key]["entrate"]

        for anno, mese, totale_spese in totali_spese:
            key = f"{anno}-{mese:02d}"
            print("spese:", key, totale_spese)
            if key in result:
                result[key]["spese"] = float(totale_spese or 0)
                result[key]["valore"] -= result[key]["spese"]

        # TRASFORMA DICTIONARY → LIST MANTENENDO ORDINE YYYY-MM
        result_list = [
            {
                "mese": key,
                "entrate": valori["entrate"],
                "spese": valori["spese"],
                "valore": valori["valore"],
                "currency": user_currency
            }
            for key, valori in result.items()
        ]

        print("result_list finale:", result_list)

        return jsonify(result_list), 200

    except Exception as e:
        print("Error total_balances_by_month:", str(e))
        return jsonify({"error": "Unable to retrieve balances"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("=== total_balances_by_month END ===")
