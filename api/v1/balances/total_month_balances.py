import logging
from datetime import date

from flask import request, jsonify

from database.connection import connect_to_database, create_cursor
from utils.users import get_user_currency

logger = logging.getLogger(__name__)

MAX_MONTHS = 120      # limite di sicurezza (10 anni)
DEFAULT_MONTHS = 12


# ---------------------------------------------------------------
# Utilità sulle date
# ---------------------------------------------------------------

def _parse_ym(value):
    """'2025-03' -> date(2025, 3, 1)"""
    y, m = value.split('-')
    return date(int(y), int(m), 1)


def _add_months(d, n):
    """Aggiunge n mesi (anche negativi) a una data al primo del mese."""
    idx = d.year * 12 + (d.month - 1) + n
    return date(idx // 12, idx % 12 + 1, 1)


def resolve_range():
    """
    Ritorna (start, end_esclusivo) come date al primo del mese.

    Priorità:
      1. ?start=YYYY-MM&end=YYYY-MM  (intervallo personalizzato)
      2. ?months=N                   (ultimi N mesi, mese corrente incluso)
      3. default: 12 mesi
    """
    start_p = request.args.get('start')
    end_p = request.args.get('end')

    if start_p or end_p:
        if not (start_p and end_p):
            raise ValueError("Specificare sia 'start' che 'end'")
        start = _parse_ym(start_p)
        end = _add_months(_parse_ym(end_p), 1)  # fine esclusiva
    else:
        months = int(request.args.get('months', DEFAULT_MONTHS))
        if months < 1:
            raise ValueError("'months' deve essere >= 1")
        end = _add_months(date.today().replace(day=1), 1)
        start = _add_months(end, -months)

    if start >= end:
        raise ValueError("'start' deve precedere 'end'")
    if (end.year - start.year) * 12 + (end.month - start.month) > MAX_MONTHS:
        raise ValueError(f"Intervallo massimo: {MAX_MONTHS} mesi")
    return start, end


# ---------------------------------------------------------------
# Query
# ---------------------------------------------------------------

# NB: si assume che valore * exchange_rate = importo nella valuta di
# default dell'utente (exchange_rate NULL => già in quella valuta).
# Se la semantica è inversa, sostituire con valore / exchange_rate.

SQL_MONTHLY = """
WITH months AS (
    SELECT generate_series(%(start)s::date,
                           %(end)s::date - interval '1 month',
                           interval '1 month')::date AS m
),
inc AS (
    SELECT date_trunc('month', giorno)::date AS m,
           SUM(valore * COALESCE(exchange_rate, 1)) AS total
    FROM entrate
    WHERE user_id = %(uid)s AND giorno >= %(start)s AND giorno < %(end)s
    GROUP BY 1
),
exp AS (
    SELECT date_trunc('month', giorno)::date AS m,
           SUM(valore * COALESCE(exchange_rate, 1)) AS total
    FROM spese
    WHERE user_id = %(uid)s AND giorno >= %(start)s AND giorno < %(end)s
    GROUP BY 1
)
SELECT to_char(months.m, 'YYYY-MM') AS month,
       COALESCE(inc.total, 0)       AS income,
       COALESCE(exp.total, 0)       AS expense
FROM months
LEFT JOIN inc ON inc.m = months.m
LEFT JOIN exp ON exp.m = months.m
ORDER BY months.m;
"""

SQL_OPENING = """
SELECT
  COALESCE((SELECT SUM(valore * COALESCE(exchange_rate, 1))
            FROM entrate
            WHERE user_id = %(uid)s AND giorno < %(start)s), 0)
  -
  COALESCE((SELECT SUM(valore * COALESCE(exchange_rate, 1))
            FROM spese
            WHERE user_id = %(uid)s AND giorno < %(start)s), 0);
"""


# ---------------------------------------------------------------
# Endpoint handler
# ---------------------------------------------------------------

def total_balances_by_month(user_id):
    logger.warning("NUOVO handler total_balances_by_month chiamato")    
    try:
        start, end = resolve_range()
    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "message": str(e)}), 400

    params = {"uid": user_id, "start": start, "end": end}

    conn = None
    cur = None
    try:
        conn = connect_to_database()
        cur = create_cursor(conn)

        cur.execute(SQL_MONTHLY, params)
        rows = cur.fetchall()

        cur.execute(SQL_OPENING, params)
        opening = float(cur.fetchone()[0])
    except Exception as e:
        logger.error(f"Errore nel calcolo dei bilanci mensili: {e}")
        if conn:
            conn.rollback()
        return jsonify({"success": False, "message": "Database error"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    # Ha una connessione propria, quindi va chiamata dopo aver chiuso la nostra
    currency = get_user_currency(user_id)

    data = []
    cumulative = opening
    for month, income, expense in rows:
        income = float(income)
        expense = float(expense)
        balance = income - expense
        cumulative += balance
        data.append({
            "month": month,
            "income": round(income, 2),
            "expense": round(expense, 2),
            "balance": round(balance, 2),
            "cumulative": round(cumulative, 2),
        })

    return jsonify({
        "start": start.strftime('%Y-%m'),
        "end": _add_months(end, -1).strftime('%Y-%m'),
        "currency": currency,
        "opening_balance": round(opening, 2),
        "data": data,
    }), 200