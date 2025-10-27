import json
import datetime
import requests
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger, EXCHANGE_API_URL, EXCHANGE_API_KEY, BASE_CURRENCY
from collections import OrderedDict


def edit_expense(id_spesa, user_id):
    data = request.json
    updated_at = datetime.datetime.utcnow()

    logger.info(f"Updating expense ID {id_spesa} for user ID {user_id}")
    logger.info(f"Request data: {data}")

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        cursor.execute("SELECT valore, currency, giorno FROM spese WHERE id = %s AND user_id = %s", (id_spesa, user_id))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "message": "Spesa non trovata o non autorizzata"}), 404

        old_valore, old_currency, old_giorno = existing

        fields_to_update = []
        values = []
        fields_json = OrderedDict()

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
                url = f"{EXCHANGE_API_URL}/historical/{giorno.strftime('%Y-%m-%d')}.json"
                params = {"app_id": EXCHANGE_API_KEY, "symbols": f"{BASE_CURRENCY},{currency}"}
                logger.info(f"Richiesta tasso di cambio: {url} {params}")
                response = requests.get(url, params=params)

                if response.status_code != 200:
                    raise Exception("Errore API tasso di cambio")

                rates = response.json().get("rates", {})
                if BASE_CURRENCY not in rates or currency not in rates:
                    raise Exception("Tassi di cambio non disponibili")

                exchange_rate = rates[BASE_CURRENCY] / rates[currency]
                valore_base = round(valore * exchange_rate, 2)

                fields_to_update.append("exchange_rate = %s")
                fields_to_update.append("valore_base = %s")
                values.extend([exchange_rate, valore_base])

                fields_json["exchange_rate"] = exchange_rate
                fields_json["valore_base"] = valore_base

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

            logger.info(f"Spesa aggiornata: {update_query}")
            return jsonify({
                "success": True,
                "message": "Spesa aggiornata correttamente",
                "updated_fields": fields_json
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
