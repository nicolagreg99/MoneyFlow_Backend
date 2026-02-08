from flask import jsonify, request
from database.connection import connect_to_database, create_cursor


def delete_asset(user_id, id_asset):
    conn = None
    cursor = None

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)

        # Check if asset exists and belongs to the user
        check_query = """
            SELECT id FROM assets
            WHERE id = %s AND user_id = %s
        """
        cursor.execute(check_query, (id_asset, user_id))
        asset = cursor.fetchone()

        if not asset:
            return jsonify({"message": "Asset not found."}), 404

        # Delete the asset
        delete_query = """
            DELETE FROM assets
            WHERE id = %s AND user_id = %s
        """
        cursor.execute(delete_query, (id_asset, user_id))

        if cursor.rowcount == 0:
            return jsonify({"message": "Failed to delete asset."}), 500

        conn.commit()

        return jsonify({"message": "Asset deleted successfully."}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({
            "message": "Failed to delete asset.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()