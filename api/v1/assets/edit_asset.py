from flask import jsonify, request
from database.connection import connect_to_database, create_cursor

def edit_asset(user_id, id_asset):
    data = request.json
    amount = data.get('amount')
    asset_type = data.get('asset_type')

    if not amount or not asset_type:
        return jsonify({"message": "Amount and asset type are required."}), 400

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)
        cursor.execute("""
            UPDATE assets
            SET amount = %s, asset_type = %s
            WHERE id = %s AND user_id = %s
        """, (amount, asset_type, id_asset, user_id))
        conn.commit()
        return jsonify({"message": "Asset updated successfully."}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
