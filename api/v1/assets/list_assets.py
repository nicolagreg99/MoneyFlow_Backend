from datetime import date
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter


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

    order_direction = order.upper()
    descending = order.lower() == "desc"

    # Sorting by amount is done in Python on the converted value (see below),
    # because it needs live exchange rates. SQL handles every other field.
    if sort_by == "amount":
        order_by_clause = "bank ASC, asset_type ASC"
    else:
        order_by_clause = f"{valid_sort_fields[sort_by]} {order_direction}"
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

        # ---------------- USER CURRENCY ----------------
        cursor.execute(
            "SELECT default_currency FROM users WHERE id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        user_currency = row[0] if row and row[0] else "EUR"

        # ---------------- ASSETS ----------------
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

        # ---------------- RATES TO USER CURRENCY (one lookup per currency) ----------------
        today = date.today()
        rates = {}

        def rate_to_user_currency(from_currency, stored_rate):
            if from_currency == user_currency:
                return 1.0
            if from_currency in rates:
                return rates[from_currency]
            try:
                rate = float(currency_converter.convert_amount(
                    1.0,
                    date=today,
                    from_currency=from_currency,
                    to_currency=user_currency
                ))
            except Exception as conv_error:
                print(f"[LIST ASSETS] Rate lookup failed for {from_currency}->{user_currency}: {conv_error}")
                # Fallback: stored rate on the asset, otherwise 1
                rate = float(stored_rate) if stored_rate else 1.0
            rates[from_currency] = rate
            return rate

        assets_list = []
        for asset in assets:
            amount = float(asset[3])
            rate = rate_to_user_currency(asset[4], asset[5])
            assets_list.append({
                "id": asset[0],
                "bank": asset[1],
                "asset_type": asset[2],
                "amount": amount,
                "currency": asset[4],
                "exchange_rate": rate,
                "amount_in_user_currency": round(amount * rate, 2),
                "user_currency": user_currency,
                "is_payable": asset[6],
                "last_updated": asset[7].isoformat() if asset[7] else None
            })

        # ---------------- SORT BY CONVERTED AMOUNT ----------------
        if sort_by == "amount":
            # Stable multi-pass sort: asset_type, then bank, then converted amount
            assets_list.sort(key=lambda a: a["asset_type"] or "")
            assets_list.sort(key=lambda a: (a["bank"] or "").lower())
            assets_list.sort(key=lambda a: a["amount_in_user_currency"], reverse=descending)

        return jsonify({
            "assets": assets_list,
            "total_count": len(assets_list),
            "sort_by": sort_by,
            "order": order,
            "user_currency": user_currency
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