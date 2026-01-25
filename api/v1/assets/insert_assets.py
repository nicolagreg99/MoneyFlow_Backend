from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def insert_assets(user_id):
    data = request.json
    bank = data.get("bank")
    currency = data.get("currency")
    amount = data.get("amount")
    asset_type = data.get("asset_type")

    if not bank or not currency or not amount or not asset_type:
        return jsonify({"message": "All fields are required."}), 400

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Check duplicate
        cursor.execute("""
            SELECT 1
            FROM assets
            WHERE user_id = %s AND bank = %s AND asset_type = %s AND currency = %s
        """, (user_id, bank, asset_type, currency))

        if cursor.fetchone():
            return jsonify({
                "message": "Asset already exists for this bank and asset type."
            }), 409  # Conflict

        # Insert
        cursor.execute("""
            INSERT INTO assets (user_id, bank, currency, amount, asset_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, bank, currency, amount, asset_type))

        conn.commit()
        return jsonify({"message": "Asset added successfully."}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({
            "message": "Failed to insert asset."
        }), 500
