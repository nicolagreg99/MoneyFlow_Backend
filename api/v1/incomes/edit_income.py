import json
import datetime
from decimal import Decimal
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from utils.currency_converter import currency_converter


def edit_income(id_entrata, user_id):
    data = request.json or {}
    updated_at = datetime.datetime.utcnow()

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # ---------------- ENTRATA ESISTENTE ----------------
        cursor.execute("""
            SELECT valore, currency, giorno, payment_asset_id
            FROM entrate
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (id_entrata, user_id))

        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "message": "Entrata non trovata"}), 404

        old_valore, old_currency, old_giorno, old_asset_id = existing
        old_valore = Decimal(str(old_valore))

        # ---------------- USER CURRENCY ----------------
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency = cursor.fetchone()[0] or "EUR"

        # ---------------- NUOVI DATI ----------------
        new_valore = Decimal(str(data.get("valore", old_valore)))
        new_currency = data.get("currency", old_currency).upper()
        giorno = (
            datetime.datetime.strptime(data["giorno"], "%Y-%m-%d").date()
            if "giorno" in data else old_giorno
        )

        new_asset_id = data.get("payment_asset_id", old_asset_id)

        # ---------------- VALIDAZIONE ASSET ----------------
        cursor.execute("""
            SELECT id, currency, amount
            FROM assets
            WHERE id = %s AND user_id = %s AND is_payable = TRUE
            FOR UPDATE
        """, (new_asset_id, user_id))

        asset = cursor.fetchone()
        if not asset:
            return jsonify({
                "success": False,
                "message": "Payment asset not found or not payable"
            }), 400

        asset_id, asset_currency, asset_amount = asset
        asset_amount = Decimal(str(asset_amount))

        # ---------------- CONVERSIONE ----------------
        def convert(amount, from_curr, to_curr, date):
            if from_curr == to_curr:
                return amount
            return Decimal(str(
                currency_converter.convert_amount(
                    float(amount),
                    date=date,
                    from_currency=from_curr,
                    to_currency=to_curr
                )
            ))

        # vecchio importo → da RIMUOVERE
        old_converted = convert(
            old_valore,
            old_currency,
            asset_currency,
            old_giorno
        )

        # nuovo importo → da AGGIUNGERE
        new_converted = convert(
            new_valore,
            new_currency,
            asset_currency,
            giorno
        )

        # ---------------- RIMOZIONE VECCHIO EFFETTO ----------------
        if old_asset_id:
            cursor.execute("""
                UPDATE assets
                SET amount = amount - %s
                WHERE id = %s
            """, (old_converted, old_asset_id))

        # ---------------- APPLICA NUOVO EFFETTO ----------------
        cursor.execute("""
            UPDATE assets
            SET amount = amount + %s
            WHERE id = %s
        """, (new_converted, asset_id))

        # ---------------- EXCHANGE RATE ----------------
        if new_currency == user_currency:
            exchange_rate = 1.0
        else:
            exchange_rate = currency_converter.get_historical_rate(
                giorno, new_currency, user_currency
            )

        # ---------------- UPDATE ENTRATA ----------------
        cursor.execute("""
            UPDATE entrate
            SET
                valore = %s,
                currency = %s,
                exchange_rate = %s,
                giorno = %s,
                payment_asset_id = %s,
                fields = %s::json,
                inserted_at = %s
            WHERE id = %s AND user_id = %s
        """, (
            new_valore,
            new_currency,
            exchange_rate,
            giorno,
            asset_id,
            json.dumps({
                "descrizione": data.get("descrizione", ""),
                "user_id": user_id
            }),
            updated_at,
            id_entrata,
            user_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Income updated successfully",
            "asset_id": asset_id,
            "asset_currency": asset_currency,
            "amount_added": float(new_converted)
        }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error editing income: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
