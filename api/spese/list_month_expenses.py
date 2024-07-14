from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

def spese_mensili():
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
        
        # Esegue la query per ottenere le spese nel mese specifico
        cursor.execute("""
            SELECT id, valore, tipo, giorno, inserted_at, user_id, fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
            ORDER BY giorno DESC
        """, (data_inizio, data_fine, user_id))
        
        spese_mensili = cursor.fetchall()
        
        if not spese_mensili:
            return jsonify({"messaggio": "Nessuna spesa effettuata nel mese specificato per l'utente specificato"}), 200
        
        spese_json = []
        for spesa in spese_mensili:
            spesa_dict = {
                "id": spesa[0],
                "valore": spesa[1],
                "tipo": spesa[2],
                "giorno": spesa[3].strftime('%Y-%m-%d'),
                "inserted_at": spesa[4].strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": spesa[5],
                "descrizione": spesa[6]  
            }
            spese_json.append(spesa_dict)
        
        return jsonify(spese_json), 200
    except Exception as e:
        print("Errore durante il recupero delle spese mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare le spese mensili"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
