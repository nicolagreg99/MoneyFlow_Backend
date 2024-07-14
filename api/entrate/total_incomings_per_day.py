from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime

conn = connect_to_database()
cursor = create_cursor(conn)

def calcola_totali_giornalieri_entrate():
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

        # Esegui la query SQL per ottenere i totali giornalieri
        query = """
            SELECT giorno, SUM(valore) AS totale_per_giorno
            FROM entrate
            WHERE giorno >= %s AND giorno < %s
              AND user_id = %s
            GROUP BY giorno;
        """
        cursor.execute(query, (start_date, end_date, user_id))
        
        # Estrai i risultati dalla query
        totali_giornalieri = cursor.fetchall()
        
        if not totali_giornalieri:
            return jsonify({"messaggio": "Nessun guadagno ricevuto nel mese e anno specificati per l'utente specificato"}), 200
        
        # Prepara la risposta JSON con i totali giornalieri
        result = [{"giorno": row[0].day, "totale_per_giorno": row[1]} for row in totali_giornalieri]
        
        return jsonify(result), 200
    
    except Exception as e:
        print("Errore durante il recupero dei totali giornalieri:", str(e))
        return jsonify({"errore": "Impossibile recuperare i totali giornalieri"}), 500
