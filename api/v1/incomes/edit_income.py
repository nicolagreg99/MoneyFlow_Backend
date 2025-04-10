import json
import datetime
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from collections import OrderedDict


def edit_income(id_entrata, user_id):
    data = request.json
    updated_at = datetime.datetime.utcnow()

    logger.info(f"Updating income ID {id_entrata} for user ID {user_id}")
    logger.info(f"Request data: {data}")

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("SELECT DISTINCT tipo FROM entrate WHERE user_id = %s", (user_id,))
        valid_types = [row[0] for row in cursor.fetchall()]
        logger.info(f"Valid 'tipo' values for user: {valid_types}")

        fields_to_update = []
        values = []

        fields_json = OrderedDict()

        if "tipo" in data:
            tipo = data["tipo"]
            if not valid_types:
                return jsonify({
                    "success": False,
                    "message": "Cannot validate 'tipo'. User has no existing types."
                }), 400
            if tipo not in valid_types:
                return jsonify({
                    "success": False,
                    "message": f"Invalid 'tipo': '{tipo}'. Allowed values: {valid_types}"
                }), 400
            fields_to_update.append("tipo = %s")
            values.append(tipo)
            fields_json["tipo"] = tipo
        else:
            fields_json["tipo"] = None

        if "valore" in data:
            fields_to_update.append("valore = %s")
            values.append(data["valore"])
            fields_json["valore"] = data["valore"]
        else:
            fields_json["valore"] = None

        if "giorno" in data:
            fields_to_update.append("giorno = %s")
            values.append(data["giorno"])
            fields_json["giorno"] = data["giorno"]
        else:
            fields_json["giorno"] = None

        fields_json["descrizione"] = data.get("descrizione", "")

        fields_json["user_id"] = user_id

        fields_to_update.append("fields = %s")
        values.append(json.dumps(fields_json))

        fields_to_update.append("inserted_at = %s")
        values.append(updated_at)

        if fields_to_update:
            values.append(id_entrata)
            update_query = f"UPDATE entrate SET {', '.join(fields_to_update)} WHERE id = %s"
            cursor.execute(update_query, tuple(values))
            logger.info(f"Executed query: {update_query}")

            conn.commit()
            logger.info("Income updated successfully")

            return jsonify({
                "success": True,
                "message": "Income updated",
                "updated_fields": fields_json
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "No valid fields provided"
            }), 400

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating income: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()