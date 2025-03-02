from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
import jwt
from datetime import datetime, timedelta

def bilancio_totale():
    try:
        # Verifica la presenza del token
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            # Decodifica il token per ottenere l'user_id
            decoded_token = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        # Connessione al database
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Query per ottenere la somma totale delle entrate
        query_entrate = """
            SELECT SUM(valore) AS totale_entrate
            FROM entrate
            WHERE user_id = %s;
        """
        cursor.execute(query_entrate, (user_id,))
        totale_entrate = cursor.fetchone()[0] or 0.00  # Se non ci sono entrate, usa 0.00

        # Query per ottenere la somma totale delle spese
        query_spese = """
            SELECT SUM(valore) AS totale_spese
            FROM spese
            WHERE user_id = %s;
        """
        cursor.execute(query_spese, (user_id,))
        totale_spese = cursor.fetchone()[0] or 0.00  # Se non ci sono spese, usa 0.00

        # Calcolo del bilancio totale
        bilancio_totale = round(float(totale_entrate) - float(totale_spese), 2)

        # Chiudi la connessione al database
        cursor.close()
        conn.close()

        # Restituisci il bilancio totale
        return jsonify({"bilancio_totale": bilancio_totale}), 200

    except Exception as e:
        print("Errore durante il calcolo del bilancio totale:", str(e))
        return jsonify({"errore": "Impossibile calcolare il bilancio totale"}), 500