import json
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def insert_income(user_id):
    """Inserisce una nuova entrata per l'utente autenticato."""
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        data = request.json
        valore = data['valore']
        tipo = data['tipo']
        giorno = data['giorno']
        descrizione = data.get('descrizione', '')

        fields = json.dumps(data)

        cursor.execute(
            "INSERT INTO entrate (valore, tipo, giorno, user_id, fields) VALUES (%s, %s, %s, %s, %s)", 
            (valore, tipo, giorno, user_id, fields)
        )

        conn.commit()
        return jsonify({"message": "Income inserted successfully!"}), 201

    except Exception as e:
        print("Error!:", str(e))
        conn.rollback()
        return jsonify({"error": "Impossible to insert the income"}), 500

    finally:
        cursor.close()
        conn.close()
