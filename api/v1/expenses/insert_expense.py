import requests
from datetime import datetime
from flask import jsonify, request
import json

from config import EXCHANGE_API_URL, EXCHANGE_API_KEY, BASE_CURRENCY
from database.connection import connect_to_database, create_cursor


def insert_expense(user_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        valore = float(data.get("valore"))
        tipo = data.get("tipo")
        giorno_str = data.get("giorno")
        currency = data.get("currency", "EUR").upper()
        fields = data.get("fields", {})

        if not valore or not tipo or not giorno_str:
            return jsonify({"error": "Valore, tipo e giorno sono obbligatori"}), 400

        giorno = datetime.strptime(giorno_str, "%Y-%m-%d").date()

        # ✅ Se la valuta è EUR, non serve chiamare l’API
        if currency == BASE_CURRENCY:
            rate = 1.0
            valore_base = valore
        else:
            # Chiamata all’API per tasso storico
            url = f"{EXCHANGE_API_URL}/historical/{giorno.strftime('%Y-%m-%d')}.json"
            params = {"app_id": EXCHANGE_API_KEY, "symbols": f"{BASE_CURRENCY},{currency}"}
            print("🌍 Chiamata cambio:", url, params)

            response = requests.get(url, params=params)
            print("📦 Status:", response.status_code)

            if response.status_code != 200:
                return jsonify({"error": "Impossibile ottenere il tasso di cambio"}), 502

            data_fx = response.json()
            rates = data_fx.get("rates", {})

            if BASE_CURRENCY not in rates or currency not in rates:
                return jsonify({"error": "Tasso di cambio non disponibile per questa valuta"}), 400

            # Calcolo del tasso rispetto all’EUR (base currency)
            usd_to_base = rates[BASE_CURRENCY]
            usd_to_currency = rates[currency]
            rate = usd_to_base / usd_to_currency
            valore_base = round(valore * rate, 2)

        # 🔗 Inserimento nel DB
        conn = connect_to_database()
        cursor = create_cursor(conn)

        query = """
            INSERT INTO spese (
                valore, 
                valore_base, 
                exchange_rate, 
                currency, 
                tipo, 
                giorno, 
                fields, 
                user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s::json, %s)
            RETURNING id;
        """

        cursor.execute(
            query,
            (valore, valore_base, rate, currency, tipo, giorno, json.dumps(fields), user_id)
        )
        conn.commit()
        new_id = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "id": new_id,
            "valore": valore,
            "valore_base_eur": valore_base,
            "exchange_rate": rate,
            "currency": currency,
            "giorno": str(giorno)
        }), 201

    except Exception as e:
        print("❌ Errore durante l'inserimento della spesa:", str(e))
        return jsonify({"error": "Errore durante l'inserimento della spesa"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
