import logging
from flask import jsonify, request
from database.connection import connect_to_database, create_cursor
from datetime import datetime, timedelta
from utils.currency_converter import currency_converter

logger = logging.getLogger(__name__)

def expenses_list(user_id):
    conn = None
    cursor = None
    local_cache = {}

    logger.info(f"Invocazione /expenses/list per user_id={user_id}")

    try:
        conn = connect_to_database()
        cursor = create_cursor(conn)
        logger.debug("Connessione al DB stabilita")

        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        tipi = request.args.getlist('tipo')

        logger.info(f"Parametri ricevuti → from_date={from_date_str}, to_date={to_date_str}, tipi={tipi}")

        if not from_date_str or not to_date_str:
            logger.warning("from_date o to_date mancanti")
            return jsonify({"error": "from_date e to_date sono richiesti"}), 400

        try:
            data_inizio = datetime.strptime(from_date_str, '%Y-%m-%d')
            data_fine = datetime.strptime(to_date_str, '%Y-%m-%d')
            logger.debug(f"Date parse riuscita: data_inizio={data_inizio}, data_fine={data_fine}")
        except ValueError as ve:
            logger.error(f"Errore parsing date: {ve}")
            return jsonify({"error": "Formato delle date non valido. Usa YYYY-MM-DD."}), 400

        if data_fine < data_inizio:
            logger.warning("Intervallo date non valido: fine < inizio")
            return jsonify({"error": "La data di fine deve essere successiva alla data di inizio"}), 400

        cursor.execute("SELECT default_currency FROM users WHERE id = %s", (user_id,))
        user_currency_result = cursor.fetchone()
        user_currency = user_currency_result[0] if user_currency_result and user_currency_result[0] else "EUR"
        logger.info(f"Valuta utente = {user_currency}")

        # Costruzione query
        query = """
            SELECT 
                id,
                valore,
                tipo,
                giorno,
                inserted_at,
                user_id,
                currency,
                exchange_rate,
                fields ->> 'descrizione' AS descrizione
            FROM spese
            WHERE giorno >= %s 
              AND giorno < %s 
              AND user_id = %s
              AND valore IS NOT NULL
        """
        params = [data_inizio, data_fine + timedelta(days=1), user_id]

        if tipi:
            placeholders = ', '.join(['%s'] * len(tipi))
            query += f" AND tipo IN ({placeholders})"
            params.extend(tipi)

        query += " ORDER BY giorno DESC"

        logger.debug(f"Eseguendo query: {query}")
        logger.debug(f"Parametri: {params}")

        cursor.execute(query, tuple(params))
        spese_mensili = cursor.fetchall()

        logger.info(f"Numero di righe trovate nel DB: {len(spese_mensili)}")

        if not spese_mensili:
            logger.info("Nessuna spesa trovata per l'intervallo specificato")
            return jsonify({
                "messaggio": "Nessuna spesa trovata nel periodo specificato",
                "default_currency": user_currency,
                "expenses": []
            }), 200

        spese_json = []
        for spesa in spese_mensili:
            if spesa[1] is not None:
                valore_originale = float(spesa[1])
                currency_spesa = spesa[6]
                exchange_rate = float(spesa[7]) if spesa[7] is not None else 1.0
                giorno = spesa[3]

                logger.debug(f"Riga DB → id={spesa[0]}, tipo={spesa[2]}, valore={valore_originale}, "
                             f"currency={currency_spesa}, giorno={giorno}")

                if currency_spesa == user_currency:
                    valore_convertito = valore_originale
                else:
                    cache_key = f"{giorno.strftime('%Y-%m-%d')}_{currency_spesa}_{user_currency}"
                    if cache_key in local_cache:
                        rate = local_cache[cache_key]
                        logger.debug(f"Rate trovato in cache locale: {cache_key} = {rate}")
                    else:
                        rate = currency_converter.get_historical_rate(
                            giorno.strftime('%Y-%m-%d'),
                            currency_spesa,
                            user_currency
                        )
                        local_cache[cache_key] = rate
                        logger.debug(f"Rate calcolato e salvato: {cache_key} = {rate}")

                    valore_convertito = round(valore_originale * rate, 2)

                logger.debug(f"Valore convertito finale: {valore_convertito}")

                spese_json.append({
                    "id": spesa[0],
                    "valore": valore_originale,
                    "converted_value": valore_convertito,
                    "tipo": spesa[2],
                    "giorno": giorno.strftime('%Y-%m-%d') if giorno else None,
                    "inserted_at": spesa[4].strftime('%Y-%m-%d %H:%M:%S') if spesa[4] else None,
                    "user_id": spesa[5],
                    "currency": currency_spesa,
                    "exchange_rate": exchange_rate,
                    "descrizione": spesa[8] if spesa[8] else "",
                    "user_currency": user_currency
                })

        logger.info(f"Totale spese elaborate: {len(spese_json)}")

        return jsonify({
            "default_currency": user_currency,
            "expenses": spese_json
        }), 200

    except Exception as e:
        logger.error(f"Errore durante il recupero delle spese: {e}", exc_info=True)
        return jsonify({
            "errore": "Impossibile recuperare le spese",
            "dettaglio": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("Connessione al DB chiusa")
