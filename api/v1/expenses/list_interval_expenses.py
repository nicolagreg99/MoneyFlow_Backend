from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta

def expenses_list(user_id):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        tipi = request.args.getlist('tipo') 
 
        if not from_date_str or not to_date_str:
            return jsonify({"error": "from_date e to_date sono richiesti"}), 400
        
        try:
            data_inizio = datetime.strptime(from_date_str, '%Y-%m-%d')
            data_fine = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato delle date non valido. Usa YYYY-MM-DD."}), 400
        
        if data_fine < data_inizio:
            return jsonify({"error": "La data di fine deve essere successiva alla data di inizio"}), 400
        
        query = """
            SELECT id, valore, tipo, giorno, inserted_at, user_id, fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s AND giorno < %s AND user_id = %s
        """
        params = [data_inizio, data_fine + timedelta(days=1), user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " ORDER BY giorno DESC"

        cursor.execute(query, tuple(params))
        spese_mensili = cursor.fetchall()
        
        if not spese_mensili:
            return jsonify({"messaggio": "Nessuna spesa effettuata nel periodo specificato per l'utente specificato"}), 200
        
        spese_json = [
            {
                "id": spesa[0],
                "valore": spesa[1],
                "tipo": spesa[2],
                "giorno": spesa[3].strftime('%Y-%m-%d'),
                "inserted_at": spesa[4].strftime('%Y-%m-%d %H:%M:%S'),
                "user_id": spesa[5],
                "descrizione": spesa[6]
            }
            for spesa in spese_mensili
        ]
        
        return jsonify(spese_json), 200

    except Exception as e:
        print("Errore durante il recupero delle spese mensili:", str(e))
        return jsonify({"errore": "Impossibile recuperare le spese mensili"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
