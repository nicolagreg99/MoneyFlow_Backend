from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

conn = connect_to_database()
cursor = create_cursor(conn)

def delete_expense(id_spesa):
    try:
        # Controlla se la spesa esiste prima di eliminarla
        cursor.execute("SELECT id FROM spese WHERE id = %s", (id_spesa,))
        expense = cursor.fetchone()

        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        # Se esiste, elimina la spesa
        cursor.execute("DELETE FROM spese WHERE id = %s", (id_spesa,))
        conn.commit()

        return jsonify({"message": "Deleted successfully!"}), 200
    except Exception as e:
        print("Error!:", str(e))
        conn.rollback()
        return jsonify({"error": "Impossible to remove the expense"}), 500
