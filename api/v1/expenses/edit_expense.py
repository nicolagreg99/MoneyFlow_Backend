import json
import datetime
import requests
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger, EXCHANGE_API_URL, EXCHANGE_API_KEY
from utils.currency_converter import currency_converter


def edit_expense(id_spesa, user_id):
    data = request.json
    updated_at = datetime.datetime.utcnow()

    logger.info(f"Updating expense ID {id_spesa} for user ID {user_id}")
    logger.info(f"Request data: {data}")

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute(
            "SELECT valore, currency, giorno FROM spese WHERE id = %s AND user_id = %s",
            (id_spesa, user_id)
        )
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "message": "Spesa non trovata o non autorizzata"}), 404

        old_valore, old_currency, old_giorno = existing

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_default_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        fields_to_update = []
        values = []
        fields_json = {}

        tipo = data.get("tipo")
        valore = float(data["valore"]) if "valore" in data else old_valore
        giorno_str = data.get("giorno")
        currency = data.get("currency", old_currency).upper()

        giorno = (
            datetime.datetime.strptime(giorno_str, "%Y-%m-%d").date()
            if giorno_str
            else old_giorno
        )

        if tipo:
            fields_to_update.append("tipo = %s")
            values.append(tipo)
            fields_json["tipo"] = tipo

        if "valore" in data:
            fields_to_update.append("valore = %s")
            values.append(valore)
            fields_json["valore"] = valore

        if "giorno" in data:
            fields_to_update.append("giorno = %s")
            values.append(giorno)
            fields_json["giorno"] = str(giorno)

        if "currency" in data:
            fields_to_update.append("currency = %s")
            values.append(currency)
            fields_json["currency"] = currency

        recalc_needed = any(k in data for k in ["valore", "currency", "giorno"])

        if recalc_needed:
            try:
                if currency == user_default_currency:
                    exchange_rate = 1.0
                else:
                    exchange_rate = currency_converter.get_historical_rate(
                        giorno, currency, user_default_currency
                    )

                fields_to_update.append("exchange_rate = %s")
                values.append(exchange_rate)
                fields_json["exchange_rate"] = exchange_rate

            except Exception as fx_error:
                logger.error(f"Errore nel calcolo tasso di cambio: {fx_error}")
                return jsonify({"success": False, "message": "Errore nel recupero del tasso di cambio"}), 500

        fields_json["descrizione"] = data.get("descrizione", "")
        fields_json["user_id"] = user_id

        fields_to_update.append("fields = %s")
        values.append(json.dumps(fields_json))

        fields_to_update.append("inserted_at = %s")
        values.append(updated_at)

        if fields_to_update:
            values.append(id_spesa)
            update_query = f"UPDATE spese SET {', '.join(fields_to_update)} WHERE id = %s"
            cursor.execute(update_query, tuple(values))
            conn.commit()

            logger.info(f"Spesa aggiornata con successo (ID {id_spesa})")
            return jsonify({
                "success": True,
                "message": "Spesa aggiornata correttamente",
                "updated_fields": fields_json,
                "currency_base": user_default_currency
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Nessun campo valido fornito"
            }), 400

    except Exception as e:
        conn.rollback()
        logger.error(f"Errore durante aggiornamento spesa: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()