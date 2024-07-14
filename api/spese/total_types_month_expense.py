from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

conn = connect_to_database()
cursor = create_cursor(conn)

def calcola_totali_mensili_per_tipo():
    try:
        user_id = request.args.get('user_id')
        mese = request.args.get('mese')
        anno = request.args.get('anno')

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        if not mese or not anno:
            return jsonify({"error": "Month and Year are required"}), 400
        
        try:
            mese = int(mese)
            anno = int(anno)
            start_date = datetime(anno, mese, 1)
            end_date = (start_date.replace(month=mese + 1) if mese < 12 else start_date.replace(year=anno + 1, month=1))
        except ValueError:
            return jsonify({"error": "Invalid Month or Year"}), 400

        # Esegui la query SQL per ottenere i totali mensili per tipo di spesa
        query = """
            SELECT tipo, SUM(valore) AS totale_per_tipo
            FROM spese
            WHERE giorno >= %s AND giorno < %s
              AND user_id = %s
            GROUP BY tipo;
        """
        cursor.execute(query, (start_date, end_date, user_id))
        
        # Estrai i risultati dalla query
        totali_mensili_per_tipo = cursor.fetchall()
        
        if not totali_mensili_per_tipo:
            return jsonify({"messaggio": "Nessuna spesa effettuata nel mese e anno specificati per l'utente specificato"}), 200
        
        # Prepara la risposta JSON con i totali mensili per tipo di spesa
        result = [{"tipo": row[0], "totale_per_tipo": row[1]} for row in totali_mensili_per_tipo]
        
        return jsonify(result), 200
    
    except Exception as e:
        print("Errore durante il recupero dei totali mensili per tipo di spesa:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali mensili per tipo di spesa"}), 500
