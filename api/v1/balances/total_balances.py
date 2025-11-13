from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
import jwt

def total_balance():
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

        conn = connect_to_database()
        cursor = create_cursor(conn)

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        query_entrate = """
            SELECT 
                SUM(valore * COALESCE(exchange_rate, 1)) AS totale_entrate
            FROM entrate
            WHERE user_id = %s;
        """
        cursor.execute(query_entrate, (user_id,))
        totale_entrate = cursor.fetchone()[0] or 0.00

        query_spese = """
            SELECT 
                SUM(valore * COALESCE(exchange_rate, 1)) AS totale_spese
            FROM spese
            WHERE user_id = %s;
        """
        cursor.execute(query_spese, (user_id,))
        totale_spese = cursor.fetchone()[0] or 0.00

        bilancio_totale = round(float(totale_entrate) - float(totale_spese), 2)

        cursor.close()
        conn.close()

        return jsonify({
            "bilancio_totale": bilancio_totale,
            "currency": user_currency
        }), 200

    except Exception as e:
        print("Errore durante il calcolo del bilancio totale:", str(e))
        return jsonify({"errore": "Impossibile calcolare il bilancio totale"}), 500
