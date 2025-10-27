from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
import logging

logger = logging.getLogger(__name__)

def total_expenses_by_day(base_currency="EUR"):
    try:
        token = request.headers.get("x-access-token")
        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            decoded_token = jwt.decode(token, "your_secret_key", algorithms=["HS256"])
            user_id = decoded_token.get("user_id")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        month = request.args.get("mese")
        year = request.args.get("anno")

        if not month or not year:
            return jsonify({"error": "Month and Year are required"}), 400

        try:
            month = int(month)
            year = int(year)
            start_date = datetime(year, month, 1)
            end_date = (
                start_date.replace(month=month + 1)
                if month < 12
                else start_date.replace(year=year + 1, month=1)
            )
        except ValueError:
            return jsonify({"error": "Invalid Month or Year"}), 400

        conn = connect_to_database()
        cursor = create_cursor(conn)

        query = """
            SELECT giorno, SUM(valore_base) AS total_per_day
            FROM spese
            WHERE giorno >= %s
              AND giorno < %s
              AND user_id = %s
            GROUP BY giorno
            ORDER BY giorno;
        """

        cursor.execute(query, (start_date, end_date, user_id))
        daily_totals = cursor.fetchall()

        if not daily_totals:
            return jsonify({"message": "No expenses found for the selected month"}), 200

        result = [
            {
                "giorno": row[0].day,
                "totale_per_giorno": round(float(row[1] or 0), 2),
                "currency": base_currency,
            }
            for row in daily_totals
        ]

        logger.info(f"Daily totals calculated for user_id={user_id}, month={month}, year={year}")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error retrieving daily totals: {e}")
        return jsonify({"error": "Unable to retrieve daily totals"}), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
