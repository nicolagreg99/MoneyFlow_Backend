import json
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

conn = connect_to_database()
cursor = create_cursor(conn)

def inserisci_spesa():
    try:
        data = request.json
        valore = data['valore']
        tipo = data['tipo']
        giorno = data['giorno']
        descrizione = data.get('descrizione', '')  # Ottieni la descrizione, se presente
        user_id = data.get('user_id')  # Seleziona l'user_id dalla richiesta, se presente

        # Registra il corpo della richiesta come parte dei campi della spesa
        fields = json.dumps(request.json)
        
        # Esegui l'inserimento della spesa nel database, incluso il corpo della richiesta
        cursor.execute("INSERT INTO spese (valore, tipo, giorno, user_id, fields) VALUES (%s, %s, %s, %s, %s)", 
                       (valore, tipo, giorno, user_id, fields))

        # Controlla se il suggerimento esiste già nel database
        cursor.execute("SELECT id FROM suggerimenti WHERE descrizione = %s AND tipo = %s AND tabella = %s",
                       (descrizione, tipo, 'spesa'))
        suggestion = cursor.fetchone()
        
        # Inserisci la nuova suggestion nel database solo se non esiste già
        if suggestion is None:
            cursor.execute("INSERT INTO suggerimenti (descrizione, tipo, tabella, user_id) VALUES (%s, %s, %s, %s)",
                           (descrizione, tipo, 'spesa', user_id))
        
        conn.commit()
        
        return jsonify({"message": "Entered successfully!"}), 201
    except Exception as e:
        print("Error!:", str(e))
        conn.rollback()
        return jsonify({"error": "Impossible to insert the expense"}), 500
