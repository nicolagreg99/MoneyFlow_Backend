from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def get_suggestions():
    tipo = request.args.get('tipo')  # Get type from query parameter
    conn = connect_to_database()
    cursor = create_cursor(conn)
    
    try:
        cursor.execute("SELECT descrizione FROM suggerimenti WHERE tipo = %s", (tipo,))
        suggestions = cursor.fetchall()
        suggestion_list = [row[0] for row in suggestions]
        return jsonify(suggestion_list), 200
    except Exception as e:
        print("Error retrieving suggestions:", str(e))
        return jsonify({"error": "Unable to retrieve suggestions"}), 500
    finally:
        cursor.close()
        conn.close()
