from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def list_assets(user_id):
    is_payable_param = request.args.get("is_payable")
    sort_by = request.args.get("sort_by", "amount")  # Default: amount
    order = request.args.get("order", "desc")  # Default: desc

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

    # ---------------- SORTING VALIDATION ----------------
    valid_sort_fields = {
        "amount": "amount",
        "currency": "currency",
        "bank": "bank",
        "asset_type": "asset_type",
        "last_updated": "last_updated"
    }

    if sort_by not in valid_sort_fields:
        return jsonify({
            "message": f"Invalid sort_by parameter. Valid options: {', '.join(valid_sort_fields.keys())}"
        }), 400

    if order.lower() not in ("asc", "desc"):
        return jsonify({
            "message": "order must be 'asc' or 'desc'."
        }), 400

    # Build ORDER BY clause
    order_direction = order.upper()
    sort_field = valid_sort_fields[sort_by]
    
    # For amount sorting, we want to sort by the converted value in EUR
    if sort_by == "amount":
        order_by_clause = f"(amount * exchange_rate) {order_direction}"
    else:
        order_by_clause = f"{sort_field} {order_direction}"
    
    # Add secondary sorting for better UX
    if sort_by != "bank":
        order_by_clause += ", bank ASC"
    if sort_by not in ("bank", "asset_type"):
        order_by_clause += ", asset_type ASC"

    where_clause = " AND ".join(filters)

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        query = f"""
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
            ORDER BY {order_by_clause}
        """

        cursor.execute(query, tuple(params))

        assets = cursor.fetchall()

        assets_list = []
        for asset in assets:
            assets_list.append({
                "id": asset[0],
                "bank": asset[1],
                "asset_type": asset[2],
                "amount": float(asset[3]),
                "currency": asset[4],
                "exchange_rate": float(asset[5]) if asset[5] else 1.0,
                "is_payable": asset[6],
                "last_updated": asset[7].isoformat() if asset[7] else None
            })

        return jsonify({
            "assets": assets_list,
            "total_count": len(assets_list),
            "sort_by": sort_by,
            "order": order
        }), 200

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