from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def insert_assets(user_id):
    data = request.json or {}

    bank = data.get("bank")
    currency = data.get("currency")
    amount = data.get("amount")
    asset_type = data.get("asset_type")
    is_payable = data.get("is_payable", False)  # default FALSE

    # ---------------- VALIDATION ----------------
    if not bank or not currency or asset_type is None or amount is None:
        return jsonify({"message": "bank, currency, asset_type and amount are required."}), 400

    try:
        amount = float(amount)
    except Exception:
        return jsonify({"message": "Invalid amount format."}), 400

    if amount < 0:
        return jsonify({"message": "Amount cannot be negative."}), 400

    if not isinstance(is_payable, bool):
        return jsonify({"message": "is_payable must be a boolean."}), 400

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # ---------------- DUPLICATE CHECK ----------------
        cursor.execute("""
            SELECT 1
            FROM assets
            WHERE user_id = %s
              AND bank = %s
              AND asset_type = %s
              AND currency = %s
        """, (user_id, bank, asset_type, currency))

        if cursor.fetchone():
            return jsonify({
                "message": "Asset already exists for this bank, asset type and currency."
            }), 409

        # ---------------- INSERT ----------------
        cursor.execute("""
            INSERT INTO assets (
                user_id,
                bank,
                currency,
                amount,
                asset_type,
                is_payable
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            bank,
            currency,
            amount,
            asset_type,
            is_payable
        ))

        conn.commit()

        return jsonify({
            "message": "Asset added successfully.",
            "asset": {
                "bank": bank,
                "asset_type": asset_type,
                "currency": currency,
                "amount": amount,
                "is_payable": is_payable
            }
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to insert asset.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
