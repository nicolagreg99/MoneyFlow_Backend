from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
import jwt

def total_expenses_by_month(base_currency="EUR"):
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

        oggi = datetime.today()
        data_inizio = (oggi - timedelta(days=365)).replace(day=1)
        data_fine = (oggi + timedelta(days=31)).replace(day=1)

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Usa direttamente valore_base (già in EUR)
        query = """
            SELECT 
                CAST(EXTRACT(YEAR FROM s.giorno) AS INTEGER) AS anno,
                CAST(EXTRACT(MONTH FROM s.giorno) AS INTEGER) AS mese,
                SUM(s.valore_base) AS totale_per_mese
            FROM spese s
            WHERE s.giorno >= %s 
              AND s.giorno < %s
              AND s.user_id = %s
              AND s.valore_base IS NOT NULL
            GROUP BY anno, mese
            ORDER BY anno, mese;
        """

        cursor.execute(query, (data_inizio, data_fine, user_id))
        totali_mensili = cursor.fetchall()

        mesi_nomi = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        result = {}
        for i in range(12):
            mese_rif = (oggi.month - i - 1) % 12 + 1
            anno_rif = oggi.year if oggi.month - i > 0 else oggi.year - 1
            result[f"{mesi_nomi[mese_rif]} {anno_rif}"] = 0.0

        for anno, mese, totale in totali_mensili:
            chiave = f"{mesi_nomi[mese]} {anno}"
            result[chiave] = round(float(totale or 0), 2)

        return jsonify({
            "currency": base_currency,
            "monthly_totals": result
        }), 200

    except Exception as e:
        print("Error while fetching monthly totals:", str(e))
        return jsonify({"error": "Unable to fetch monthly totals", "detail": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
