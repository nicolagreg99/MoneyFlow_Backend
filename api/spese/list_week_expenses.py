from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

def spese_settimanali():
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Calcola la data 7 giorni fa rispetto alla data corrente
        data_inizio_settimana = datetime.now() - timedelta(days=7)
        
        # Esegue la query per ottenere le spese entro gli ultimi 7 giorni per l'utente specifico
        cursor.execute("""
            SELECT id, valore, tipo, giorno, inserted_at, user_id, fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s
              AND user_id = %s
            ORDER BY giorno DESC
        """, (data_inizio_settimana, user_id))
        
        # Recupera il risultato della query
        spese_settimanali = cursor.fetchall()
        
        if not spese_settimanali:
            return jsonify({"messaggio": "Nessuna spesa effettuata nell'ultima settimana per l'utente specificato"}), 200
        
        # Converte il risultato in un formato JSON
        spese_json = []
        for spesa in spese_settimanali:
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
        print("Errore durante il recupero delle spese settimanali:", str(e))
        return jsonify({"errore": "Impossibile recuperare le spese settimanali"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
