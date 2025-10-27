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
            SELECT 
                id,
                valore,
                tipo,
                giorno,
                inserted_at,
                user_id,
                currency,
                valore_base,
                exchange_rate,
                fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s 
              AND giorno < %s 
              AND user_id = %s
              AND valore IS NOT NULL
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
            return jsonify({"messaggio": "Nessuna spesa trovata nel periodo specificato"}), 200
        
        spese_json = [
            {
                "id": spesa[0],
                "valore": float(spesa[1]) if spesa[1] is not None else None,
                "tipo": spesa[2],
                "giorno": spesa[3].strftime('%Y-%m-%d') if spesa[3] else None,
                "inserted_at": spesa[4].strftime('%Y-%m-%d %H:%M:%S') if spesa[4] else None,
                "user_id": spesa[5],
                "currency": spesa[6],
                "valore_base": float(spesa[7]) if spesa[7] is not None else None,
                "exchange_rate": float(spesa[8]) if spesa[8] is not None else None,
                "descrizione": spesa[9] if spesa[9] else ""
            }
            for spesa in spese_mensili
            if spesa[1] is not None
        ]
        
        return jsonify(spese_json), 200

    except Exception as e:
        print("Errore durante il recupero delle spese:", str(e))
        return jsonify({
            "errore": "Impossibile recuperare le spese",
            "dettaglio": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
