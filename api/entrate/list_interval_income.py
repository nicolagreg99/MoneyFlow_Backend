from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
import jwt

def incomings_interval():
    conn = None
    cursor = None
    
    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded_token = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
            user_id = decoded_token.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        if not user_id:
            return jsonify({"error": "User ID is missing from token"}), 401

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        tipo = request.args.get('tipo')  

        if not from_date_str or not to_date_str:
            return jsonify({"error": "from_date and to_date are required"}), 400
        
        try:
            data_inizio = datetime.strptime(from_date_str, '%Y-%m-%d')
            data_fine = datetime.strptime(to_date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        
        if data_fine < data_inizio:
            return jsonify({"error": "End date must be after start date"}), 400
        
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

        cursor.execute(query, tuple(params))
        
        entrate_mensili = cursor.fetchall()
        
        if not entrate_mensili:
            return jsonify({"message": "No entries found for the specified period and user"}), 200
        
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
        print("Error fetching incoming entries:", str(e))
        return jsonify({"error": "Unable to fetch incoming entries"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
