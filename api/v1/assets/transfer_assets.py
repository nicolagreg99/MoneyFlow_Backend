from flask import jsonify, request
from decimal import Decimal, InvalidOperation
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


def transfer_assets(user_id):
    data = request.json or {}

    from_bank = data.get("from_bank")
    from_asset_type = data.get("from_asset_type")
    from_currency = data.get("from_currency")

    to_bank = data.get("to_bank")
    to_asset_type = data.get("to_asset_type")
    to_currency = data.get("to_currency")

    amount = data.get("amount")

    # ---------------- VALIDATION ----------------
    if not all([
        from_bank, from_asset_type, from_currency,
        to_bank, to_asset_type, to_currency,
        amount
    ]):
        return jsonify({
            "message": (
                "from_bank, from_asset_type, from_currency, "
                "to_bank, to_asset_type, to_currency and amount are required."
            )
        }), 400

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return jsonify({"message": "Invalid amount format."}), 400

    if amount <= 0:
        return jsonify({"message": "Amount must be greater than zero."}), 400

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # ---------------- SOURCE ASSET (LOCKED) ----------------
        cursor.execute("""
            SELECT id, amount, currency
            FROM assets
            WHERE user_id = %s
              AND bank = %s
              AND asset_type = %s
              AND currency = %s
            FOR UPDATE
        """, (user_id, from_bank, from_asset_type, from_currency))

        source = cursor.fetchone()
        if not source:
            return jsonify({
                "message": (
                    f"Source asset not found "
                    f"({from_bank} - {from_asset_type} - {from_currency})."
                )
            }), 404

        source_id, source_amount, source_currency = source
        source_amount = Decimal(str(source_amount))

        if source_amount < amount:
            return jsonify({"message": "Insufficient funds in source asset."}), 400

        # ---------------- DESTINATION ASSET (LOCKED) ----------------
        cursor.execute("""
            SELECT id, currency
            FROM assets
            WHERE user_id = %s
              AND bank = %s
              AND asset_type = %s
              AND currency = %s
            FOR UPDATE
        """, (user_id, to_bank, to_asset_type, to_currency))

        destination = cursor.fetchone()
        if not destination:
            return jsonify({
                "message": (
                    f"Destination asset not found "
                    f"({to_bank} - {to_asset_type} - {to_currency})."
                )
            }), 404

        dest_id, dest_currency = destination

        # ---------------- CURRENCY CONVERSION ----------------
        if source_currency != dest_currency:
            converted_amount = Decimal(str(
                currency_converter.convert_amount(
                    float(amount),
                    date=None,
                    from_currency=source_currency,
                    to_currency=dest_currency
                )
            ))
            exchange_rate = (converted_amount / amount).quantize(Decimal("0.000001"))
        else:
            converted_amount = amount
            exchange_rate = Decimal("1.0")

        # ---------------- TRANSACTION TYPE ----------------
        if from_bank == to_bank and from_asset_type != to_asset_type:
            transaction_type = "INVEST"
        else:
            transaction_type = "TRANSFER"

        # ---------------- UPDATE SOURCE ----------------
        cursor.execute("""
            UPDATE assets
            SET amount = amount - %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (amount, source_id))

        # ---------------- UPDATE DESTINATION ----------------
        cursor.execute("""
            UPDATE assets
            SET amount = amount + %s,
                last_updated = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (converted_amount, dest_id))

        # ---------------- REGISTER TRANSACTION ----------------
        cursor.execute("""
            INSERT INTO asset_transactions (
                user_id,
                from_asset_id,
                to_asset_id,
                amount,
                converted_amount,
                from_currency,
                to_currency,
                transaction_type,
                exchange_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            source_id,
            dest_id,
            amount,
            converted_amount,
            source_currency,
            dest_currency,
            transaction_type,
            exchange_rate
        ))

        conn.commit()

        return jsonify({
            "message": "Transfer completed successfully.",
            "transaction_type": transaction_type,
            "from": {
                "bank": from_bank,
                "asset_type": from_asset_type,
                "currency": source_currency,
                "amount": float(amount)
            },
            "to": {
                "bank": to_bank,
                "asset_type": to_asset_type,
                "currency": dest_currency,
                "amount": float(converted_amount)
            }
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Transfer failed.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
