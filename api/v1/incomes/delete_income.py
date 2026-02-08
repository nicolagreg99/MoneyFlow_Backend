import datetime
from decimal import Decimal
from flask import jsonify
from database.connection import connect_to_database, create_cursor
from config import logger
from utils.currency_converter import currency_converter


def delete_income(id_entrata, user_id):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        # ---------------- RECUPERA ENTRATA ESISTENTE ----------------
        cursor.execute("""
            SELECT valore, currency, giorno, payment_asset_id
            FROM entrate
            WHERE id = %s AND user_id = %s
            FOR UPDATE
        """, (id_entrata, user_id))

        income = cursor.fetchone()
        if not income:
            return jsonify({"error": "Income not found"}), 404

        valore, currency, giorno, asset_id = income
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
                asset_amount = Decimal(str(asset_amount))

                # Converti l'importo dell'entrata nella valuta dell'asset
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

                # Controlla che ci siano fondi sufficienti
                if asset_amount < converted_amount:
                    return jsonify({
                        "error": "Insufficient funds in asset to remove income",
                        "asset_balance": float(asset_amount),
                        "required": float(converted_amount)
                    }), 400

                # RIMUOVI l'importo dall'asset (l'entrata viene cancellata)
                cursor.execute("""
                    UPDATE assets
                    SET amount = amount - %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (converted_amount, asset_id))

                logger.info(
                    f"Removed {converted_amount} {asset_currency} from asset {asset_id} "
                    f"for deleted income {id_entrata}"
                )

        # ---------------- ELIMINA L'ENTRATA ----------------
        cursor.execute("DELETE FROM entrate WHERE id = %s AND user_id = %s", (id_entrata, user_id))
        conn.commit()

        return jsonify({
            "message": "Income deleted successfully",
            "asset_updated": asset_id is not None
        }), 200

    except Exception as e:
        logger.error(f"Error deleting income: {e}")
        conn.rollback()
        return jsonify({"error": "Impossible to remove the income", "details": str(e)}), 500

    finally:
        cursor.close()
        conn.close()