import json
from datetime import datetime
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


def insert_income(user_id):
    """Inserisce una nuova entrata per l'utente autenticato."""
    conn = None
    cursor = None

    try:
        data = request.get_json()
        valore = data.get("valore")
        tipo = data.get("tipo")
        giorno_str = data.get("giorno")
        currency = data.get("currency", "").upper()
        descrizione = data.get("descrizione") or data.get("description") or ""
        fields = data.get("fields", {})

        if not valore or not tipo or not giorno_str:
            return jsonify({"error": "Valore, tipo e giorno sono obbligatori"}), 400

        valore = float(valore)
        giorno = datetime.strptime(giorno_str, "%Y-%m-%d").date()

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Recupera la valuta di default dell'utente
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        # Se non è stata specificata la currency, usa quella dell'utente
        if not currency:
            currency = user_currency

        # Calcola il tasso di cambio
        if currency == user_currency:
            exchange_rate = 1.0
        else:
            exchange_rate = currency_converter.get_historical_rate(
                giorno, currency, user_currency
            )

        # ✅ Crea un JSON completo per la colonna fields
        fields.update({
            "tipo": tipo,
            "valore": valore,
            "currency": currency,
            "exchange_rate": exchange_rate,
            "descrizione": descrizione,
            "user_id": user_id
        })

        cursor.execute(
            """
            INSERT INTO entrate (
                valore,
                tipo,
                giorno,
                user_id,
                fields,
                currency,
                exchange_rate
            )
            VALUES (%s, %s, %s, %s, %s::json, %s, %s)
            RETURNING id;
            """,
            (valore, tipo, giorno, user_id, json.dumps(fields), currency, exchange_rate)
        )

        new_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Income inserted successfully!",
            "id": new_id,
            "valore": valore,
            "currency": currency,
            "exchange_rate": exchange_rate,
            "user_currency": user_currency,
            "giorno": str(giorno),
            "fields": fields
        }), 201

    except Exception as e:
        print("❌ Error inserting income:", str(e))
        if conn:
            conn.rollback()
        return jsonify({"error": "Impossible to insert the income", "details": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
