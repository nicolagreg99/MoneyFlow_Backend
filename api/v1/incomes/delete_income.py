from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

conn = connect_to_database()
cursor = create_cursor(conn)

def cancella_entrata(id_guadagno):
    try:
        # Esegui la query per eliminare la riga corrispondente all'id_guadagno specificato
        cursor.execute("DELETE FROM entrate WHERE id = %s", (id_guadagno,))
        
        # Conferma la transazione e applica le modifiche al database
        conn.commit()
        
        return jsonify({"message": "Deleted successfully!"}), 200
    except Exception as e:
        print("Error!:", str(e))
        # In caso di errore, annulla le modifiche e restituisci un messaggio di errore
        conn.rollback()
        return jsonify({"error": "Impossible to remove the income"}), 500

