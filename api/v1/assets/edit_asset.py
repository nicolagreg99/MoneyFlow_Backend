from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def edit_asset(user_id, id_asset):
    data = request.json or {}

    amount = data.get("amount")
    bank = data.get("bank")
    asset_type = data.get("asset_type")
    is_payable = data.get("is_payable")

    # ---------------- NOTHING TO UPDATE ----------------
    if amount is None and bank is None and asset_type is None and is_payable is None:
        return jsonify({
            "message": "At least one field must be provided (amount, bank, asset_type, is_payable)."
        }), 400

    fields = []
    params = []

    # ---------------- VALIDATION ----------------
    if amount is not None:
        try:
            amount = float(amount)
        except Exception:
            return jsonify({"message": "Invalid amount format."}), 400

        if amount < 0:
            return jsonify({"message": "Amount cannot be negative."}), 400

        fields.append("amount = %s")
        params.append(amount)

    if bank is not None:
        bank = bank.strip()
        if not bank:
            return jsonify({"message": "Bank name cannot be empty."}), 400

        fields.append("bank = %s")
        params.append(bank)

    if asset_type is not None:
        fields.append("asset_type = %s")
        params.append(asset_type)

    if is_payable is not None:
        if not isinstance(is_payable, bool):
            return jsonify({"message": "is_payable must be a boolean."}), 400

        fields.append("is_payable = %s")
        params.append(is_payable)

    # Always update timestamp
    fields.append("last_updated = CURRENT_TIMESTAMP")

    params.extend([id_asset, user_id])

    query = f"""
        UPDATE assets
        SET {", ".join(fields)}
        WHERE id = %s AND user_id = %s
    """

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        cursor.execute(query, tuple(params))

        if cursor.rowcount == 0:
            return jsonify({"message": "Asset not found."}), 404

        conn.commit()

        return jsonify({"message": "Asset updated successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to update asset.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()