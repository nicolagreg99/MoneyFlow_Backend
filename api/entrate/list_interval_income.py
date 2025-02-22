from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

def incomings_interval(current_user_id):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        user_id = current_user_id  # Passato direttamente dal decoratore

        # Recupera parametri dalla query string
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        tipo = request.args.get('tipo')

        # Verifica parametri obbligatori
        if not from_date_str or not to_date_str:
            return jsonify({"error": "from_date e to_date sono richiesti"}), 400

        # Parsing delle date
        try:
            data_inizio = datetime.strptime(from_date_str, '%Y-%m-%d')
            data_fine = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato delle date non valido. Usa YYYY-MM-DD."}), 400

        # Controllo validità intervallo date
        if data_fine < data_inizio:
            return jsonify({"error": "La data di fine deve essere successiva alla data di inizio"}), 400

        # Query SQL per recuperare le entrate
        query = """
            SELECT id, valore, tipo, giorno, inserted_at, user_id, fields ->> 'descrizione' AS descrizione
            FROM entrate
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
        """
        params = [data_inizio, data_fine + timedelta(days=1), user_id]

        if tipo:
            query += " AND tipo = %s"
            params.append(tipo)

        query += " ORDER BY giorno DESC"

        # Esecuzione della query
        cursor.execute(query, tuple(params))
        entrate_mensili = cursor.fetchall()

        # Nessuna entrata trovata
        if not entrate_mensili:
            return jsonify({"messaggio": "Nessuna entrata registrata nel periodo specificato"}), 200

        # Costruzione della risposta JSON
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
