import json
import datetime
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from utils.currency_converter import currency_converter

def edit_income(id_entrata, user_id):
    data = request.json
    updated_at = datetime.datetime.utcnow()

    logger.info(f"Updating income ID {id_entrata} for user ID {user_id}")
    logger.info(f"Request data: {data}")

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # Recupera l'entrata esistente
        cursor.execute(
            "SELECT valore, currency, giorno FROM entrate WHERE id = %s AND user_id = %s",
            (id_entrata, user_id)
        )
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "message": "Entrata non trovata"}), 404

        old_valore, old_currency, old_giorno = existing

        # Recupera valuta utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        # Validazione tipi
        cursor.execute("SELECT DISTINCT tipo FROM entrate WHERE user_id = %s", (user_id,))
        valid_types = [row[0] for row in cursor.fetchall()]
        logger.info(f"Valid 'tipo' values for user: {valid_types}")

        fields_to_update = []
        values = []

        # Prepara i dati per l'aggiornamento
        tipo = data.get("tipo")
        valore = float(data["valore"]) if "valore" in data else old_valore
        giorno_str = data.get("giorno")
        currency = data.get("currency", old_currency).upper()

        giorno = (
            datetime.datetime.strptime(giorno_str, "%Y-%m-%d").date()
            if giorno_str
            else old_giorno
        )

        # Validazione tipo
        if "tipo" in data:
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

        if "valore" in data:
            fields_to_update.append("valore = %s")
            values.append(valore)

        if "giorno" in data:
            fields_to_update.append("giorno = %s")
            values.append(giorno)

        if "currency" in data:
            fields_to_update.append("currency = %s")
            values.append(currency)

        # Ricalcola exchange_rate se necessario
        recalc_needed = any(k in data for k in ["valore", "currency", "giorno"])
        if recalc_needed:
            try:
                if currency == user_currency:
                    exchange_rate = 1.0
                else:
                    exchange_rate = currency_converter.get_historical_rate(
                        giorno, currency, user_currency
                    )
                fields_to_update.append("exchange_rate = %s")
                values.append(exchange_rate)
            except Exception as fx_error:
                logger.error(f"Errore nel calcolo tasso di cambio: {fx_error}")
                return jsonify({"success": False, "message": "Errore nel recupero del tasso di cambio"}), 500

        # Aggiorna fields
        descrizione = data.get("descrizione", "")
        fields_json = {
            "descrizione": descrizione,
            "user_id": user_id
        }
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
                "message": "Income updated successfully",
                "updated_fields": fields_json,
                "currency_base": user_currency
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