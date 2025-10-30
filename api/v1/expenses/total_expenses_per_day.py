from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime
import jwt
import logging
from utils.currency_converter import currency_converter

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

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"

        query = """
            SELECT giorno, SUM(valore), currency, exchange_rate
            FROM spese
            WHERE giorno >= %s
              AND giorno < %s
              AND user_id = %s
            GROUP BY giorno, currency, exchange_rate
            ORDER BY giorno;
        """

        cursor.execute(query, (start_date, end_date, user_id))
        daily_totals = cursor.fetchall()

        if not daily_totals:
            return jsonify({"message": "No expenses found for the selected month"}), 200

        daily_totals_converted = {}
        for row in daily_totals:
            giorno = row[0]
            totale = float(row[1] or 0)
            currency_spesa = row[2]
            exchange_rate = float(row[3]) if row[3] is not None else 1.0

            if currency_spesa == user_currency:
                totale_convertito = totale
            else:
                totale_convertito = currency_converter.convert_amount(
                    totale, 
                    row[0],  # giorno
                    currency_spesa, 
                    user_currency
                )

            if giorno in daily_totals_converted:
                daily_totals_converted[giorno] += totale_convertito
            else:
                daily_totals_converted[giorno] = totale_convertito

        result = [
            {
                "giorno": giorno.day,
                "totale_per_giorno": round(totale, 2),
                "currency": user_currency,
            }
            for giorno, totale in daily_totals_converted.items()
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