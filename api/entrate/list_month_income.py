from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

def entrate_mensili():
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
        
        # Esegue la query per ottenere le entrate nel mese specifico
        cursor.execute("""
            SELECT id, valore, tipo, giorno, inserted_at, user_id, fields ->> 'descrizione' AS descrizione
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            ORDER BY giorno DESC
        """, (data_inizio, data_fine, user_id))
        
        entrate_mensili = cursor.fetchall()
        
        if not entrate_mensili:
            return jsonify({"messaggio": "Nessuna entrata effettuata nel mese specificato per l'utente specificato"}), 200
        
        entrate_json = []
        for entrata in entrate_mensili:
            entrata_dict = {
                "id": entrata[0],
                "valore": entrata[1],
                "tipo": entrata[2],
                "giorno": entrata[3].strftime('%Y-%m-%d'),
                "inserted_at": entrata[4].strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": entrata[5],
                "descrizione": entrata[6]  
            }
            entrate_json.append(entrata_dict)
        
        return jsonify(entrate_json), 200
    except Exception as e:
        print("Errore durante il recupero delle entrate mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare le entrate mensili"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
