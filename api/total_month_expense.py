from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

conn = connect_to_database()
cursor = create_cursor(conn)

def totali_mensili():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Calcola la data del primo giorno del mese corrente
        data_inizio_mese = datetime.now().replace(day=1)
        
        # Esegue la query per ottenere la somma dei valori delle spese entro l'intero mese corrente per l'utente specifico
        cursor.execute("SELECT SUM(valore) FROM spese WHERE EXTRACT(MONTH FROM giorno) = EXTRACT(MONTH FROM %s) AND EXTRACT(YEAR FROM giorno) = EXTRACT(YEAR FROM %s) AND user_id = %s", 
                       (data_inizio_mese, data_inizio_mese, user_id))
        
        # Recupera il risultato della query
        totali_mensili = cursor.fetchone()[0]
        
        if totali_mensili is None:
            return jsonify({"messaggio": "Nessuna spesa effettuata nell'ultimo mese per l'utente specificato"}), 200
        
        return jsonify({"totale_mensile": totali_mensili}), 200
    except Exception as e:
        print("Errore durante il recupero dei totali mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili"}), 500
