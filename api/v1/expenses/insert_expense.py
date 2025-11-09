import requests
from datetime import datetime
from flask import jsonify, request
import json

from config import EXCHANGE_API_URL, EXCHANGE_API_KEY
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


def insert_expense(user_id):
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

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        if not currency:
            currency = user_currency

        if currency == user_currency:
            exchange_rate = 1.0
        else:
            exchange_rate = currency_converter.get_historical_rate(
                giorno, currency, user_currency
            )

        # ✅ Creiamo un JSON completo da salvare nella colonna fields
        fields.update({
            "tipo": tipo,
            "valore": valore,
            "currency": currency,
            "exchange_rate": exchange_rate,
            "descrizione": descrizione,
            "user_id": user_id
        })

        query = """
            INSERT INTO spese (
                valore,
                exchange_rate,
                currency,
                tipo,
                giorno,
                fields,
                user_id
            )
            VALUES (%s, %s, %s, %s, %s, %s::json, %s)
            RETURNING id;
        """

        cursor.execute(
            query,
            (valore, exchange_rate, currency, tipo, giorno, json.dumps(fields), user_id)
        )
        conn.commit()

        new_id = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "id": new_id,
            "valore": valore,
            "exchange_rate": exchange_rate,
            "currency": currency,
            "user_currency": user_currency,
            "giorno": str(giorno),
            "fields": fields
        }), 201

    except Exception as e:
        print("❌ Error while inserting expense:", str(e))
        return jsonify({"error": "Error while inserting expense", "details": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()