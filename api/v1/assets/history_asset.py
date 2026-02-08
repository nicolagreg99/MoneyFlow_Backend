from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def history_asset(user_id, id_asset):
    limit = request.args.get("limit", 50)
    
    try:
        limit = int(limit)
        if limit <= 0 or limit > 500:
            limit = 50
    except (ValueError, TypeError):
        limit = 50

    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Get the specific asset
        cursor.execute("""
            SELECT id, bank, asset_type, currency
            FROM assets
            WHERE user_id = %s AND id = %s
        """, (user_id, id_asset))
        
        asset = cursor.fetchone()
        
        if not asset:
            return jsonify({
                "message": "Asset not found."
            }), 404
        
        asset_id, bank, asset_type, asset_currency = asset
        
        # Get all transactions: expenses and incomes
        query = """
            (
                SELECT
                    'EXPENSE' as source,
                    s.id,
                    s.tipo as transaction_type,
                    'OUTFLOW' as flow_type,
                    s.valore as amount,
                    s.currency,
                    s.exchange_rate,
                    s.giorno as date,
                    s.fields::jsonb as fields
                FROM spese s
                WHERE s.payment_asset_id = %s
                  AND s.user_id = %s
            )
            UNION ALL
            (
                SELECT
                    'INCOME' as source,
                    e.id,
                    e.tipo as transaction_type,
                    'INFLOW' as flow_type,
                    e.valore as amount,
                    e.currency,
                    e.exchange_rate,
                    e.giorno as date,
                    e.fields
                FROM entrate e
                WHERE e.payment_asset_id = %s
                  AND e.user_id = %s
            )
            ORDER BY date DESC
            LIMIT %s
        """
        
        cursor.execute(query, (asset_id, user_id, asset_id, user_id, limit))
        
        transactions = cursor.fetchall()
        
        transactions_list = []
        total_inflow = 0
        total_outflow = 0
        
        for tx in transactions:
            source = tx[0]
            tx_id = tx[1]
            transaction_type = tx[2]
            flow_type = tx[3]
            amount = float(tx[4])
            tx_currency = tx[5]
            exchange_rate = float(tx[6]) if tx[6] else 1.0
            date = tx[7].isoformat() if tx[7] else None
            fields = tx[8]
            
            # Convert amount to asset currency
            converted_amount = amount * exchange_rate
            
            if flow_type == "OUTFLOW":
                total_outflow += converted_amount
            else:
                total_inflow += converted_amount
            
            transaction_data = {
                "id": tx_id,
                "source": source,
                "type": transaction_type,
                "flow_type": flow_type,
                "amount": amount,
                "currency": tx_currency,
                "exchange_rate": exchange_rate,
                "date": date,
                "fields": fields
            }
            
            transactions_list.append(transaction_data)
        
        return jsonify({
            "asset": {
                "id": asset_id,
                "bank": bank,
                "asset_type": asset_type,
                "currency": asset_currency
            },
            "transactions": transactions_list,
            "total_count": len(transactions_list),
            "summary": {
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "net_flow": total_inflow - total_outflow
            }
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to retrieve asset history.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()    