from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def get_suggestions():
    tipo = request.args.get('tipo')  # Ottieni il tipo dal parametro di query
    tabella = request.args.get('tabella')  # Ottieni la tabella dal parametro di query
    conn = connect_to_database()
    cursor = create_cursor(conn)
    
    try:
        cursor.execute("SELECT descrizione, user_id FROM suggerimenti WHERE tipo = %s AND tabella = %s", (tipo, tabella))
        suggestions = cursor.fetchall()
        
        # Crea una lista di dizionari con descrizione e user_id
        suggestion_list = [{"descrizione": row[0], "user_id": row[1]} for row in suggestions]
        
        return jsonify(suggestion_list), 200
    except Exception as e:
        print("Error retrieving suggestions:", str(e))
        return jsonify({"error": "Unable to retrieve suggestions"}), 500
    finally:
        cursor.close()
        conn.close()
