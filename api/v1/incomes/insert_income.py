import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


def insert_income(user_id):
    conn = None
    cursor = None

    try:
        data = request.get_json() or {}

        valore = data.get("valore")
        tipo = data.get("tipo")
        giorno_str = data.get("giorno")
        currency = (data.get("currency") or "").upper()
        descrizione = data.get("descrizione") or data.get("description") or ""
        payment_asset_id = data.get("payment_asset_id")
        fields = data.get("fields", {})

        # ---------------- VALIDATION ----------------
        if not all([valore, tipo, giorno_str, payment_asset_id]):
            return jsonify({
                "error": "Valore, tipo, giorno e payment_asset_id sono obbligatori"
            }), 400

        try:
            valore = Decimal(str(valore))
        except (InvalidOperation, TypeError):
            return jsonify({"error": "Formato valore non valido"}), 400

        if valore <= 0:
            return jsonify({"error": "Il valore deve essere maggiore di zero"}), 400

        giorno = datetime.strptime(giorno_str, "%Y-%m-%d").date()

        conn = connect_to_database()
        cursor = create_cursor(conn)

        # ---------------- USER DEFAULT CURRENCY ----------------
        cursor.execute(
            "SELECT default_currency FROM users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        if not currency:
            currency = user_currency

        # ---------------- TARGET ASSET (LOCKED) ----------------
        cursor.execute("""
            SELECT id, amount, currency, is_payable
            FROM assets
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (payment_asset_id, user_id))

        asset = cursor.fetchone()
        if not asset:
            return jsonify({"error": "Asset di destinazione non trovato"}), 404

        asset_id, asset_amount, asset_currency, is_payable = asset

        if not is_payable:
            return jsonify({"error": "Asset non utilizzabile per operazioni"}), 400

        asset_amount = Decimal(str(asset_amount))

        # ---------------- CURRENCY CONVERSION ----------------
        if currency == asset_currency:
            converted_amount = valore
            exchange_rate = Decimal("1.0")
        else:
            converted_amount = Decimal(str(
                currency_converter.convert_amount(
                    float(valore),
                    date=giorno,
                    from_currency=currency,
                    to_currency=asset_currency
                )
            ))
            exchange_rate = (converted_amount / valore).quantize(Decimal("0.000001"))

        # ---------------- UPDATE ASSET (ADD MONEY) ----------------
        cursor.execute("""
            UPDATE assets
            SET amount = amount + %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (converted_amount, asset_id))

        # ---------------- FIELDS JSON ----------------
        fields.update({
            "tipo": tipo,
            "valore": float(valore),
            "currency": currency,
            "exchange_rate": float(exchange_rate),
            "converted_amount": float(converted_amount),
            "asset_currency": asset_currency,
            "descrizione": descrizione,
            "payment_asset_id": asset_id,
            "user_id": user_id
        })

        # ---------------- INSERT INCOME ----------------
        cursor.execute("""
            INSERT INTO entrate (
                valore,
                tipo,
                giorno,
                user_id,
                fields,
                currency,
                exchange_rate,
                payment_asset_id
            )
            VALUES (%s, %s, %s, %s, %s::json, %s, %s, %s)
            RETURNING id;
        """, (
            valore,
            tipo,
            giorno,
            user_id,
            json.dumps(fields),
            currency,
            exchange_rate,
            asset_id
        ))

        income_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "success": True,
            "id": income_id,
            "valore": float(valore),
            "currency": currency,
            "converted_amount": float(converted_amount),
            "asset_currency": asset_currency,
            "exchange_rate": float(exchange_rate),
            "giorno": str(giorno),
            "payment_asset_id": asset_id
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        print("❌ Error inserting income:", str(e))
        return jsonify({
            "error": "Errore durante l'inserimento dell'entrata",
            "details": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
