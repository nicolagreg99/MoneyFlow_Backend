from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from utils.currency_converter import currency_converter

def total_assets(user_id):
    group_by = request.args.get("group_by")
    asset_type_filter = request.args.get("asset_type")

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # 1️⃣ valuta di default utente
        cursor.execute("""
            SELECT default_currency
            FROM users
            WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({"message": "User not found"}), 404

        default_currency = row[0]

        # 2️⃣ assets
        query = """
            SELECT bank, asset_type, amount, currency, last_updated
            FROM assets
            WHERE user_id = %s
        """
        params = [user_id]

        if asset_type_filter:
            query += " AND asset_type = %s"
            params.append(asset_type_filter)

        cursor.execute(query, tuple(params))
        assets = cursor.fetchall()

        if not assets:
            return jsonify({"total": 0}), 200

        # 3️⃣ calcolo
        total = 0.0
        grouped = {}

        for bank, asset_type, amount, currency, date in assets:
            amount = float(amount)

            if currency != default_currency:
                amount = currency_converter.convert_amount(
                    amount=amount,
                    date=date,
                    from_currency=currency,
                    to_currency=default_currency
                )

            if group_by:
                key = {
                    "bank": bank,
                    "asset_type": asset_type,
                    "currency": currency
                }.get(group_by)

                if key not in grouped:
                    grouped[key] = 0.0

                grouped[key] += amount
            else:
                total += amount

        # 4️⃣ risposta
        if group_by:
            return jsonify({
                "group_by": group_by,
                "currency": default_currency,
                "results": [
                    {group_by: k, "total": round(v, 2)}
                    for k, v in grouped.items()
                ]
            }), 200

        return jsonify({
            "total": round(total, 2),
            "currency": default_currency
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to calculate assets total",
            "error": str(e)
        }), 500
