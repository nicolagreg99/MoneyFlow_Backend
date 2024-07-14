from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

def totali_mensili():
    conn = None
    cursor = None
    
    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Legge il mese e l'anno dai parametri della richiesta
        mese = request.args.get('mese', type=int)
        anno = request.args.get('anno', type=int)
        if not mese or not anno:
            return jsonify({"error": "Mese e Anno sono richiesti"}), 400
        
        # Calcola la data di inizio e di fine del mese
        data_inizio = datetime(anno, mese, 1)
        data_fine = datetime(anno, mese + 1, 1) if mese < 12 else datetime(anno + 1, 1, 1)
        
        # Esegue la query per ottenere la somma delle spese nel mese specifico
        cursor.execute("""
            SELECT SUM(valore)
            FROM spese
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
        """, (data_inizio, data_fine, user_id))
        
        totali_mensili = cursor.fetchone()[0]
        
        if totali_mensili is None:
            return jsonify({"messaggio": "Nessuna spesa effettuata nel mese specificato per l'utente specificato"}), 200
        
        return jsonify({"totale_mensile": totali_mensili}), 200
    except Exception as e:
        print("Errore durante il recupero dei totali mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
