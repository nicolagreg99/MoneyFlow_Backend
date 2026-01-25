import json
import datetime
from decimal import Decimal
from flask import request, jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from utils.currency_converter import currency_converter


def edit_expense(id_spesa, user_id):
    data = request.json or {}
    updated_at = datetime.datetime.utcnow()

    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # ---------------- SPESA ESISTENTE ----------------
        cursor.execute("""
            SELECT valore, currency, giorno, payment_asset_id
            FROM spese
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (id_spesa, user_id))

        existing = cursor.fetchone()
        if not existing:
            return jsonify({"success": False, "message": "Spesa non trovata"}), 404

        old_valore, old_currency, old_giorno, old_asset_id = existing
        old_valore = Decimal(str(old_valore))

        # ---------------- USER CURRENCY ----------------
        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency = cursor.fetchone()[0] or "EUR"

        # ---------------- NUOVI VALORI ----------------
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

        # vecchio importo → da RESTITUIRE
        old_converted = convert(
            old_valore,
            old_currency,
            asset_currency,
            old_giorno
        )

        # nuovo importo → da SCALARE
        new_converted = convert(
            new_valore,
            new_currency,
            asset_currency,
            giorno
        )

        # ---------------- RIPRISTINO VECCHIO ASSET ----------------
        if old_asset_id:
            cursor.execute("""
                UPDATE assets
                SET amount = amount + %s
                WHERE id = %s
            """, (old_converted, old_asset_id))

        # ---------------- SCALA DAL NUOVO ASSET ----------------
        if asset_amount < new_converted:
            return jsonify({
                "success": False,
                "message": "Insufficient funds in selected asset"
            }), 400

        cursor.execute("""
            UPDATE assets
            SET amount = amount - %s
            WHERE id = %s
        """, (new_converted, asset_id))

        # ---------------- EXCHANGE RATE ----------------
        if new_currency == user_currency:
            exchange_rate = 1.0
        else:
            exchange_rate = currency_converter.get_historical_rate(
                giorno, new_currency, user_currency
            )

        # ---------------- UPDATE SPESA ----------------
        cursor.execute("""
            UPDATE spese
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
            id_spesa,
            user_id
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Expense updated successfully",
            "asset_id": asset_id,
            "asset_currency": asset_currency,
            "amount_removed": float(new_converted)
        }), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Error editing expense: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
