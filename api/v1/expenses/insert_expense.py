from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import jsonify, request
import json

from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


def insert_expense(user_id):
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        # ---------------- BASE FIELDS ----------------
        valore = data.get("valore")
        tipo = data.get("tipo")
        giorno_str = data.get("giorno")
        currency = (data.get("currency") or "").upper()
        descrizione = data.get("descrizione") or data.get("description") or ""
        fields = data.get("fields", {})
        payment_asset_id = data.get("payment_asset_id")

        # ---------------- VALIDATION ----------------
        if valore is None or not tipo or not giorno_str or not payment_asset_id:
            return jsonify({
                "error": "valore, tipo, giorno e payment_asset_id sono obbligatori"
            }), 400

        try:
            valore = Decimal(str(valore))
        except (InvalidOperation, TypeError):
            return jsonify({"error": "Formato valore non valido"}), 400

        if valore <= 0:
            return jsonify({"error": "Il valore deve essere maggiore di zero"}), 400

        try:
            giorno = datetime.strptime(giorno_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato data non valido (YYYY-MM-DD)"}), 400

        # ---------------- DB ----------------
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # ---------------- USER CURRENCY ----------------
        cursor.execute(
            "SELECT default_currency FROM users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        if not currency:
            currency = user_currency

        # ---------------- PAYMENT ASSET (LOCKED) ----------------
        cursor.execute("""
            SELECT id, amount, currency, is_payable
            FROM assets
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (payment_asset_id, user_id))

        asset = cursor.fetchone()
        if not asset:
            return jsonify({"error": "Asset di pagamento non trovato"}), 404

        asset_id, asset_amount, asset_currency, is_payable = asset
        asset_amount = Decimal(str(asset_amount))

        if not is_payable:
            return jsonify({"error": "Questo asset non è utilizzabile per pagamenti"}), 400

        # ---------------- CURRENCY CONVERSION ----------------
        if currency == asset_currency:
            paid_amount = valore
            exchange_rate = Decimal("1.0")
        else:
            paid_amount = Decimal(str(
                currency_converter.convert_amount(
                    float(valore),
                    date=giorno,
                    from_currency=currency,
                    to_currency=asset_currency
                )
            ))
            exchange_rate = (paid_amount / valore).quantize(Decimal("0.000001"))

        # ---------------- FUNDS CHECK ----------------
        if asset_amount < paid_amount:
            return jsonify({
                "error": "Fondi insufficienti sull'asset selezionato"
            }), 400

        # ---------------- UPDATE ASSET ----------------
        cursor.execute("""
            UPDATE assets
            SET amount = amount - %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (paid_amount, asset_id))

        # ---------------- FIELDS JSON ----------------
        fields.update({
            "descrizione": descrizione
        })

        # ---------------- INSERT EXPENSE ----------------
        cursor.execute("""
            INSERT INTO spese (
                valore,
                exchange_rate,
                currency,
                tipo,
                giorno,
                fields,
                user_id,
                payment_asset_id
            )
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s)
            RETURNING id
        """, (
            valore,
            exchange_rate,
            currency,
            tipo,
            giorno,
            json.dumps(fields),
            user_id,
            asset_id
        ))

        expense_id = cursor.fetchone()[0]
        conn.commit()

        # ---------------- RESPONSE ----------------
        return jsonify({
            "success": True,
            "id": expense_id,
            "tipo": tipo,
            "valore": float(valore),
            "currency": currency,
            "paid_amount": float(paid_amount),
            "paid_currency": asset_currency,
            "payment_asset_id": asset_id,
            "giorno": str(giorno)
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ Error while inserting expense:", str(e))
        return jsonify({
            "error": "Errore durante inserimento spesa",
            "details": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
