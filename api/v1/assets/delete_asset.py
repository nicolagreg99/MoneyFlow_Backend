from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def delete_asset(user_id, id_asset):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        print(f"[DELETE ASSET] Starting deletion for asset_id={id_asset}, user_id={user_id}")

        # Check if asset exists and belongs to the user
        check_query = """
            SELECT id FROM assets
            WHERE id = %s AND user_id = %s
        """
        cursor.execute(check_query, (id_asset, user_id))
        asset = cursor.fetchone()

        if not asset:
            print(f"[DELETE ASSET] Asset not found: asset_id={id_asset}, user_id={user_id}")
            return jsonify({"message": "Asset not found."}), 404

        print(f"[DELETE ASSET] Asset found: {asset}")

        # Check linked transactions
        check_transactions_query = """
            SELECT id, from_asset_id, to_asset_id, transaction_type
            FROM asset_transactions
            WHERE from_asset_id = %s OR to_asset_id = %s
        """
        cursor.execute(check_transactions_query, (id_asset, id_asset))
        linked_transactions = cursor.fetchall()
        print(f"[DELETE ASSET] Found {len(linked_transactions)} linked transaction(s): {linked_transactions}")

        # Check linked spese
        check_spese_query = """
            SELECT id, payment_asset_id
            FROM spese
            WHERE payment_asset_id = %s
        """
        cursor.execute(check_spese_query, (id_asset,))
        linked_spese = cursor.fetchall()
        print(f"[DELETE ASSET] Found {len(linked_spese)} linked spese: {linked_spese}")

        # Delete related transactions
        delete_transactions_query = """
            DELETE FROM asset_transactions
            WHERE from_asset_id = %s OR to_asset_id = %s
        """
        cursor.execute(delete_transactions_query, (id_asset, id_asset))
        print(f"[DELETE ASSET] Deleted {cursor.rowcount} transaction(s) linked to asset_id={id_asset}")

        # Nullify payment_asset_id in spese
        nullify_spese_query = """
            UPDATE spese
            SET payment_asset_id = NULL
            WHERE payment_asset_id = %s AND user_id = %s
        """
        cursor.execute(nullify_spese_query, (id_asset, user_id))
        print(f"[DELETE ASSET] Nullified payment_asset_id in {cursor.rowcount} spese row(s)")

        # Delete the asset
        delete_query = """
            DELETE FROM assets
            WHERE id = %s AND user_id = %s
        """
        cursor.execute(delete_query, (id_asset, user_id))
        print(f"[DELETE ASSET] Asset deletion affected {cursor.rowcount} row(s)")

        if cursor.rowcount == 0:
            print(f"[DELETE ASSET] ERROR: Asset deletion returned 0 rows affected")
            return jsonify({"message": "Failed to delete asset."}), 500

        conn.commit()
        print(f"[DELETE ASSET] Success: asset_id={id_asset} deleted and transaction committed")

        return jsonify({"message": "Asset deleted successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"[DELETE ASSET] EXCEPTION: {str(e)}")
        return jsonify({
            "message": "Failed to delete asset.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print(f"[DELETE ASSET] Connection closed for asset_id={id_asset}")