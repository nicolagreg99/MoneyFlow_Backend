import requests
from datetime import datetime, timedelta
from config import EXCHANGE_API_URL, EXCHANGE_API_KEY
from database.connection import connect_to_database, create_cursor

class CurrencyConverter:
    def __init__(self):
        self.cache = {}

    def get_historical_rate(self, date, from_currency, to_currency):
        if from_currency == to_currency:
            return 1.0

        if isinstance(date, datetime):
            date_str = date.strftime("%Y-%m-%d")
        else:
            date_str = str(date).split(" ")[0]

        cache_key = f"{date_str}_{from_currency}_{to_currency}"

        if cache_key in self.cache:
            print(f"Trovato in cache memoria: {cache_key} = {self.cache[cache_key]}")
            return self.cache[cache_key]

        db_rate = self._get_rate_from_db(date_str, from_currency, to_currency)
        if db_rate is not None:
            print(f"Trovato in cache DB: {cache_key} = {db_rate}")
            self.cache[cache_key] = db_rate
            return db_rate

        today = datetime.utcnow().strftime("%Y-%m-%d")
        if date_str != today:
            last_available = self._get_last_available_rate(from_currency, to_currency)
            if last_available is not None:
                print(f"Usato ultimo tasso disponibile in DB per {from_currency}->{to_currency}: {last_available}")
                self.cache[cache_key] = last_available
                return last_available

        try:
            url = f"{EXCHANGE_API_URL}/historical/{date_str}.json"
            params = {
                "app_id": EXCHANGE_API_KEY,
                "base": "USD",
                "symbols": f"{from_currency},{to_currency}"
            }

            print(f"Chiamando API per tasso: {url}")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                print(f"Errore API: {response.status_code} - {response.text}")
                return self._get_fallback_rate(from_currency, to_currency)

            data = response.json()
            rates = data.get("rates", {})

            if not rates or from_currency not in rates or to_currency not in rates:
                print(f"Valute non trovate nella risposta API: {from_currency} o {to_currency}")
                return self._get_fallback_rate(from_currency, to_currency)

            exchange_rate = rates[to_currency] / rates[from_currency]
            print(f"Tasso calcolato: 1 {from_currency} = {exchange_rate:.6f} {to_currency}")

            self._save_rate_to_db(date_str, from_currency, to_currency, exchange_rate)
            self.cache[cache_key] = exchange_rate
            return exchange_rate

        except requests.exceptions.RequestException as e:
            print(f"Errore di rete chiamando API OpenExchangeRates: {e}")
            return self._get_fallback_rate(from_currency, to_currency)
        except Exception as e:
            print(f"Errore generico nel get_historical_rate: {e}")
            return self._get_fallback_rate(from_currency, to_currency)

    def _get_rate_from_db(self, date, from_currency, to_currency):
        conn = None
        cursor = None
        try:
            conn = connect_to_database()
            cursor = create_cursor(conn)
            cursor.execute("""
                SELECT exchange_rate FROM exchange_rates_cache
                WHERE base_currency = %s AND target_currency = %s AND rate_date = %s
            """, (from_currency, to_currency, date))
            result = cursor.fetchone()
            return float(result[0]) if result else None
        except Exception as e:
            print(f"Errore lettura cache DB: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _get_last_available_rate(self, from_currency, to_currency):
        conn = None
        cursor = None
        try:
            conn = connect_to_database()
            cursor = create_cursor(conn)
            cursor.execute("""
                SELECT exchange_rate FROM exchange_rates_cache
                WHERE base_currency = %s AND target_currency = %s
                ORDER BY rate_date DESC LIMIT 1
            """, (from_currency, to_currency))
            result = cursor.fetchone()
            return float(result[0]) if result else None
        except Exception as e:
            print(f"Errore lettura ultimo tasso DB: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _save_rate_to_db(self, date, from_currency, to_currency, rate):
        conn = None
        cursor = None
        try:
            conn = connect_to_database()
            cursor = create_cursor(conn)
            cursor.execute("""
                INSERT INTO exchange_rates_cache
                (base_currency, target_currency, rate_date, exchange_rate)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (base_currency, target_currency, rate_date)
                DO UPDATE SET exchange_rate = EXCLUDED.exchange_rate
            """, (from_currency, to_currency, date, rate))
            conn.commit()
            print(f"Tasso salvato in cache DB: {from_currency}->{to_currency} = {rate}")
        except Exception as e:
            print(f"Errore salvataggio cache DB: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def convert_amount(self, amount, date, from_currency, to_currency):
        rate = self.get_historical_rate(date, from_currency, to_currency)
        converted = amount * rate
        return round(converted, 2)

    def _get_fallback_rate(self, from_currency, to_currency):
        fallback_rates = {
            ('EUR', 'USD'): 1.08,
            ('USD', 'EUR'): 0.93,
            ('EUR', 'ALL'): 115.0,
            ('ALL', 'EUR'): 0.0087,
            ('EUR', 'AED'): 3.96,
            ('AED', 'EUR'): 0.25,
            ('EUR', 'ARS'): 1050.0,
            ('ARS', 'EUR'): 0.00095,
            ('EUR', 'AUD'): 1.62,
            ('AUD', 'EUR'): 0.62,
            ('EUR', 'BGN'): 1.96,
            ('BGN', 'EUR'): 0.51,
            ('EUR', 'BRL'): 5.45,
            ('BRL', 'EUR'): 0.18,
            ('EUR', 'CAD'): 1.47,
            ('CAD', 'EUR'): 0.68,
            ('EUR', 'CHF'): 0.95,
            ('CHF', 'EUR'): 1.05,
            ('EUR', 'CNY'): 7.75,
            ('CNY', 'EUR'): 0.13,
            ('EUR', 'CZK'): 25.2,
            ('CZK', 'EUR'): 0.04,
            ('EUR', 'DKK'): 7.45,
            ('DKK', 'EUR'): 0.13,
            ('EUR', 'DZD'): 144.0,
            ('DZD', 'EUR'): 0.0069,
            ('EUR', 'EGP'): 52.0,
            ('EGP', 'EUR'): 0.019,
            ('EUR', 'GBP'): 0.86,
            ('GBP', 'EUR'): 1.16,
            ('EUR', 'HRK'): 7.53,
            ('HRK', 'EUR'): 0.13,
            ('EUR', 'HUF'): 389.0,
            ('HUF', 'EUR'): 0.0026,
            ('EUR', 'INR'): 91.0,
            ('INR', 'EUR'): 0.011,
            ('EUR', 'ISK'): 150.0,
            ('ISK', 'EUR'): 0.0066,
            ('EUR', 'JPY'): 162.0,
            ('JPY', 'EUR'): 0.0062,
            ('EUR', 'MAD'): 10.8,
            ('MAD', 'EUR'): 0.093,
            ('EUR', 'MXN'): 19.3,
            ('MXN', 'EUR'): 0.052,
            ('EUR', 'NOK'): 11.6,
            ('NOK', 'EUR'): 0.086,
            ('EUR', 'PLN'): 4.34,
            ('PLN', 'EUR'): 0.23,
            ('EUR', 'RON'): 4.97,
            ('RON', 'EUR'): 0.20,
            ('EUR', 'RSD'): 117.0,
            ('RSD', 'EUR'): 0.0085,
            ('EUR', 'RUB'): 97.0,
            ('RUB', 'EUR'): 0.0103,
            ('EUR', 'SAR'): 4.05,
            ('SAR', 'EUR'): 0.247,
            ('EUR', 'SEK'): 11.4,
            ('SEK', 'EUR'): 0.088,
            ('EUR', 'TRY'): 35.5,
            ('TRY', 'EUR'): 0.028,
            ('EUR', 'ZAR'): 19.5,
            ('ZAR', 'EUR'): 0.051,
        }

        key = (from_currency, to_currency)
        if key in fallback_rates:
            print(f"Usando fallback rate: {fallback_rates[key]}")
            return fallback_rates[key]
        print("Tasso non trovato, uso 1.0")
        return 1.0


currency_converter = CurrencyConverter()
