from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

conn = connect_to_database()
cursor = create_cursor(conn)

def totali_settimanali_per_tipo():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        # Esegui la query SQL per ottenere i totali settimanali per tipo di spesa
        query = """
            SELECT tipo, SUM(valore) AS totale_per_tipo
            FROM spese
            WHERE giorno >= now() - interval '7 day'
              AND user_id = %s
            GROUP BY tipo;
        """
        cursor.execute(query, (user_id,))
        
        # Estrai i risultati dalla query
        totali_settimanali_per_tipo = cursor.fetchall()
        
        if not totali_settimanali_per_tipo:
            return jsonify({"messaggio": "Nessuna spesa effettuata nell'ultima settimana per l'utente specificato"}), 200
        
        # Prepara la risposta JSON con i totali settimanali per tipo di spesa
        result = [{"tipo": row[0], "totale_per_tipo": row[1]} for row in totali_settimanali_per_tipo]
        
        return jsonify(result), 200
    
    except Exception as e:
        print("Errore durante il recupero dei totali settimanali per tipo di spesa:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali settimanali per tipo di spesa"}), 500
