import requests
from datetime import datetime
from config import EXCHANGE_API_URL, EXCHANGE_API_KEY
from database.connection import connect_to_database, create_cursor

class CurrencyConverter:
    def __init__(self):
        self.cache = {} 
    
    def get_historical_rate(self, date, from_currency, to_currency):
        """Ottiene il tasso di cambio per una data specifica"""
        
        if from_currency == to_currency:
            return 1.0
        
        cache_key = f"{date}_{from_currency}_{to_currency}"
        
        # 1. Controlla cache in memoria
        if cache_key in self.cache:
            print(f"Trovato in cache memoria: {cache_key} = {self.cache[cache_key]}")
            return self.cache[cache_key]
        
        # 2. Controlla cache database
        db_rate = self._get_rate_from_db(date, from_currency, to_currency)
        if db_rate is not None:
            print(f"Trovato in cache DB: {cache_key} = {db_rate}")
            self.cache[cache_key] = db_rate
            return db_rate
        
        try:
            # 3. Chiama API esterna
            url = f"{EXCHANGE_API_URL}/historical/{date}.json"
            params = {
                "app_id": EXCHANGE_API_KEY,
                "base": "USD",
                "symbols": f"{from_currency},{to_currency}"
            }
            
            print(f"Chiamando API per tasso: {url}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                print(f"Errore API: {response.status_code}")
                return self._get_fallback_rate(from_currency, to_currency)
            
            data = response.json()
            rates = data.get("rates", {})
            
            if from_currency not in rates or to_currency not in rates:
                print(f"Valute non trovate: {from_currency} o {to_currency}")
                return self._get_fallback_rate(from_currency, to_currency)
            
            exchange_rate = rates[to_currency] / rates[from_currency]

            
            print(f"Tasso calcolato: 1 {from_currency} = {exchange_rate} {to_currency}")
            
            # 4. Salva in cache DB e memoria
            self._save_rate_to_db(date, from_currency, to_currency, exchange_rate)
            self.cache[cache_key] = exchange_rate
            
            return exchange_rate
            
        except Exception as e:
            print(f"Errore nel get_historical_rate: {e}")
            return self._get_fallback_rate(from_currency, to_currency)
    
    def _get_rate_from_db(self, date, from_currency, to_currency):
        """Recupera tasso dalla cache del database"""
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
    
    def _save_rate_to_db(self, date, from_currency, to_currency, rate):
        """Salva tasso nella cache del database"""
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
        """Converte un amount da una valuta all'altra"""
        rate = self.get_historical_rate(date, from_currency, to_currency)
        converted = amount * rate
        return round(converted, 2)
    
    def _get_fallback_rate(self, from_currency, to_currency):
        """Tassi di fallback per casi di errore"""
        fallback_rates = {
            ('EUR', 'USD'): 1.08,
            ('USD', 'EUR'): 0.93,
            ('EUR', 'ALL'): 115.0,
            ('ALL', 'EUR'): 0.0087,
        }
        
        key = (from_currency, to_currency)
        if key in fallback_rates:
            print(f"Usando fallback rate: {fallback_rates[key]}")
            return fallback_rates[key]
        
        print("Tasso non trovato, uso 1.0")
        return 1.0

currency_converter = CurrencyConverter()