from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

conn = connect_to_database()
cursor = create_cursor(conn)

def totali_settimanali():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        data_inizio_settimana = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT SUM(valore) FROM spese WHERE giorno >= %s AND user_id = %s", 
                       (data_inizio_settimana, user_id))
        
        totali_settimanali = cursor.fetchone()[0]
        
        if totali_settimanali is None:
            return jsonify({"messaggio": "Nessuna spesa effettuata nell'ultima settimana per l'utente specificato"}), 200
        
        return jsonify({"totale_settimanale": totali_settimanali}), 200
    except Exception as e:
        print("Errore durante il recupero dei totali settimanali:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali settimanali"}), 500
