import json
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def insert_expense(user_id):  
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        data = request.json
        valore = data['valore']
        tipo = data['tipo']
        giorno = data['giorno']
        descrizione = data.get('descrizione', '')

        fields = json.dumps(request.json)
        
        cursor.execute(
            "INSERT INTO spese (valore, tipo, giorno, user_id, fields) VALUES (%s, %s, %s, %s, %s)", 
            (valore, tipo, giorno, user_id, fields)
        )
        
        conn.commit()
        
        return jsonify({"message": "Expense entered successfully!"}), 201
    except Exception as e:
        print("Error:", str(e))
        conn.rollback()
        return jsonify({"error": "Impossible to insert the expense"}), 500
    finally:
        cursor.close()
        conn.close()
