from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt

def totali_mensili_entrate():
    conn = None
    cursor = None
    
    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

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

        if not user_id:
            return jsonify({"error": "User ID is missing from token"}), 401

        # Legge il mese e l'anno dai parametri della richiesta
        mese = request.args.get('mese', type=int)
        anno = request.args.get('anno', type=int)
        if not mese or not anno:
            return jsonify({"error": "Mese e Anno sono richiesti"}), 400
        
        # Calcola la data di inizio e di fine del mese
        data_inizio = datetime(anno, mese, 1)
        data_fine = datetime(anno, mese + 1, 1) if mese < 12 else datetime(anno + 1, 1, 1)
        
        # Esegue la query per ottenere la somma delle entrate nel mese specifico
        cursor.execute("""
            SELECT SUM(valore)
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
        """, (data_inizio, data_fine, user_id))
        
        totali_mensili_entrate = cursor.fetchone()[0]
        
        if totali_mensili_entrate is None:
            return jsonify({"messaggio": "Nessuna entrata registrata nel mese specificato per l'utente specificato"}), 200
        
        return jsonify({"totale_mensile_entrate": totali_mensili_entrate}), 200
    except Exception as e:
        print("Errore durante il recupero dei totali mensili delle entrate:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili delle entrate"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
