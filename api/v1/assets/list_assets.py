from flask import jsonify
from database.connection import connect_to_database, create_cursor

def list_assets(user_id):
    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)
        cursor.execute("""
            SELECT id, bank, asset_type, amount, currency, exchange_rate, last_updated
            FROM assets WHERE user_id = %s
        """, (user_id,))
        assets = cursor.fetchall()

        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": asset[0],  # id asset
                "bank": asset[1],  # bank name (e.g., Revolut)
                "asset_type": asset[2],  # type of asset (e.g., Investimenti)
                "amount": asset[3],  # amount of the asset
                "currency": asset[4],  # currency (e.g., EUR)
                "exchange_rate": asset[5],  # exchange rate (default 1.0)
                "last_updated": asset[6]  # last updated timestamp
            })
        return jsonify(assets_list), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500
