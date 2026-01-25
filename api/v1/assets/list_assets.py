from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def list_assets(user_id):
    is_payable_param = request.args.get("is_payable")

    filters = ["user_id = %s"]
    params = [user_id]

    # ---------------- OPTIONAL FILTER ----------------
    if is_payable_param is not None:
        if is_payable_param.lower() not in ("true", "false"):
            return jsonify({
                "message": "is_payable must be true or false."
            }), 400

        is_payable = is_payable_param.lower() == "true"
        filters.append("is_payable = %s")
        params.append(is_payable)

    where_clause = " AND ".join(filters)

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        cursor.execute(f"""
            SELECT
                id,
                bank,
                asset_type,
                amount,
                currency,
                exchange_rate,
                is_payable,
                last_updated
            FROM assets
            WHERE {where_clause}
            ORDER BY bank, asset_type, currency
        """, tuple(params))

        assets = cursor.fetchall()

        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": asset[0],
                "bank": asset[1],
                "asset_type": asset[2],
                "amount": asset[3],
                "currency": asset[4],
                "exchange_rate": asset[5],
                "is_payable": asset[6],
                "last_updated": asset[7]
            })

        return jsonify(assets_list), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to list assets.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
