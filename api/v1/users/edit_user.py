import json
import datetime
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor

def edit_user(user_id):
    """Modifica nome, cognome e categorie di spesa/entrata per un utente autenticato."""
    data = request.json
    updated_at = datetime.datetime.utcnow()

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # Aggiorna il nome e cognome dell'utente
        fields = []
        values = []

        if "first_name" in data:
            fields.append("first_name = %s")
            values.append(data["first_name"])

        if "last_name" in data:
            fields.append("last_name = %s")
            values.append(data["last_name"])

        if fields:
            fields.append("updated_at = %s")
            values.append(updated_at)
            values.append(user_id)

            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            print(f"🔍 Query UPDATE users: {query} - {values}")  # LOG PER DEBUG
            cursor.execute(query, tuple(values))

        # Controlla se l'utente ha già un record in user_categories
        cursor.execute("SELECT * FROM user_categories WHERE user_id = %s", (user_id,))
        exists = cursor.fetchone()

        expenses_json = json.dumps(data.get("expenses", []))
        incomes_json = json.dumps(data.get("incomes", []))

        if exists:
            # Se esiste, aggiorniamo
            update_query = """
                UPDATE user_categories 
                SET expenses_categories = %s, incomes_categories = %s 
                WHERE user_id = %s
            """
            print(f"🔍 Query UPDATE user_categories: {update_query} - {expenses_json}, {incomes_json}, {user_id}")  # LOG
            cursor.execute(update_query, (expenses_json, incomes_json, user_id))
        else:
            # Se non esiste, creiamo il record
            insert_query = """
                INSERT INTO user_categories (user_id, expenses_categories, incomes_categories) 
                VALUES (%s, %s, %s)
            """
            print(f"🔍 Query INSERT user_categories: {insert_query} - {user_id}, {expenses_json}, {incomes_json}")  # LOG
            cursor.execute(insert_query, (user_id, expenses_json, incomes_json))

        conn.commit()
        print("✅ Database aggiornato con successo!")
        return jsonify({"success": True, "message": "User updated successfully"}), 200

    except Exception as e:
        conn.rollback()
        print(f"❌ Errore nel salvataggio: {e}")
        return jsonify({"success": False, "message": "Error updating user"}), 500
    finally:
        cursor.close()
        conn.close()
