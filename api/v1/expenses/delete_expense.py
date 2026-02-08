import datetime
from decimal import Decimal
from flask import jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from utils.currency_converter import currency_converter


def delete_expense(id_spesa, user_id):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # ---------------- RECUPERA SPESA ESISTENTE ----------------
        cursor.execute("""
            SELECT valore, currency, giorno, payment_asset_id
            FROM spese
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (id_spesa, user_id))

        expense = cursor.fetchone()
        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        valore, currency, giorno, asset_id = expense
        valore = Decimal(str(valore))

        # ---------------- SE C'È UN ASSET ASSOCIATO ----------------
        if asset_id:
            # Recupera info asset
            cursor.execute("""
                SELECT currency, amount
                FROM assets
                WHERE id = %s AND user_id = %s
                FOR UPDATE
            """, (asset_id, user_id))

            asset = cursor.fetchone()
            if asset:
                asset_currency, asset_amount = asset

                # Converti l'importo della spesa nella valuta dell'asset
                if currency == asset_currency:
                    converted_amount = valore
                else:
                    converted_amount = Decimal(str(
                        currency_converter.convert_amount(
                            float(valore),
                            date=giorno,
                            from_currency=currency,
                            to_currency=asset_currency
                        )
                    ))

                # RESTITUISCI l'importo all'asset (la spesa viene cancellata)
                cursor.execute("""
                    UPDATE assets
                    SET amount = amount + %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (converted_amount, asset_id))

                logger.info(
                    f"Restored {converted_amount} {asset_currency} to asset {asset_id} "
                    f"from deleted expense {id_spesa}"
                )

        # ---------------- ELIMINA LA SPESA ----------------
        cursor.execute("DELETE FROM spese WHERE id = %s AND user_id = %s", (id_spesa, user_id))
        conn.commit()

        return jsonify({
            "message": "Expense deleted successfully",
            "asset_restored": asset_id is not None
        }), 200

    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        conn.rollback()
        return jsonify({"error": "Impossible to remove the expense", "details": str(e)}), 500

    finally:
        cursor.close()
        conn.close()