from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

conn = connect_to_database()
cursor = create_cursor(conn)

def delete_income(id_entrata):
    try:
        # Controlla se l'entrata esiste prima di eliminarla
        cursor.execute("SELECT id FROM entrate WHERE id = %s", (id_entrata,))
        income = cursor.fetchone()

        if not income:
            return jsonify({"error": "Income not found"}), 404

        # Se esiste, elimina l'entrata
        cursor.execute("DELETE FROM entrate WHERE id = %s", (id_entrata,))
        conn.commit()

        return jsonify({"message": "Deleted successfully!"}), 200
    except Exception as e:
        print("Error!:", str(e))
        conn.rollback()
        return jsonify({"error": "Impossible to remove the income"}), 500
