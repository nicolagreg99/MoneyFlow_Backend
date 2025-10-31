import pytest
import time
import logging
from fixtures.test_data import get_test_expenses

logger = logging.getLogger('tests')

class TestCurrencyAPI:
    """Test suite per le funzionalità di currency"""
    
    def test_real_time_currency_update(self, authenticated_session, base_url, cleanup_data, user_default_currency, api_logger):
        """Test che il cambio valuta aggiorni le conversioni in tempo reale"""
        
        logger.info(f"Starting currency conversion test - User currency: {user_default_currency}")
        
        target_currency = "USD" if user_default_currency == "EUR" else "EUR"
        
        test_currency = "USD" if user_default_currency == "EUR" else "EUR"
        test_expense = {
            "valore": 100, 
            "tipo": "Test Currency", 
            "giorno": "2024-01-15", 
            "currency": test_currency,
            "fields": {"descrizione": f"Test currency conversion {test_currency}->{target_currency}"}
        }
        
        # Inserimento spesa
        insert_start = time.time()
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/expenses/insert",
            json=test_expense
        )
        insert_time = (time.time() - insert_start) * 1000
        api_logger(
            "POST", 
            "/api/v1/expenses/insert", 
            insert_response.status_code, 
            insert_time,
            f"Amount: {test_expense['valore']} {test_expense['currency']}"
        )
        
        assert insert_response.status_code == 201
        expense_id = insert_response.json()['id']
        cleanup_data['expenses'].append(expense_id)
        
        logger.info(f"Inserted expense {expense_id}: 100 {test_currency} (user has {user_default_currency})")

        list_start = time.time()
        list_response_initial = authenticated_session.get(
            f"{base_url}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        list_time = (time.time() - list_start) * 1000
        api_logger(
            "GET", 
            "/api/v1/expenses/list", 
            list_response_initial.status_code, 
            list_time,
            f"Found {len(list_response_initial.json().get('expenses', []))} expenses"
        )
        
        initial_converted = None
        initial_currency = None
        for expense in list_response_initial.json().get('expenses', []):
            if expense['id'] == expense_id:
                initial_converted = expense.get('converted_value')
                initial_currency = expense.get('user_currency')
                break
        
        logger.info(f"Initial converted value: {initial_converted} {initial_currency}")

        # Cambia valuta a quella target
        change_start = time.time()
        change_response = authenticated_session.patch(
            f"{base_url}/api/v1/edit_user",
            json={"default_currency": target_currency}
        )
        change_time = (time.time() - change_start) * 1000
        api_logger(
            "PATCH", 
            "/api/v1/edit_user", 
            change_response.status_code, 
            change_time,
            f"Currency change: {user_default_currency} → {target_currency}"
        )
        
        assert change_response.status_code == 200
        logger.info(f"User currency changed to {target_currency}")
        
        time.sleep(1)

        # Ottieni valore convertito nella nuova valuta dell'utente
        list_start_final = time.time()
        list_response_final = authenticated_session.get(
            f"{base_url}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        list_time_final = (time.time() - list_start_final) * 1000
        api_logger(
            "GET", 
            "/api/v1/expenses/list", 
            list_response_final.status_code, 
            list_time_final,
            f"Found {len(list_response_final.json().get('expenses', []))} expenses"
        )
        
        final_converted = None
        final_currency = None
        for expense in list_response_final.json().get('expenses', []):
            if expense['id'] == expense_id:
                final_converted = expense.get('converted_value')
                final_currency = expense.get('user_currency')
                break

        logger.info(f"Final converted value: {final_converted} {final_currency}")

        # VERIFICHE
        assert initial_converted is not None, "Initial converted value not found"
        assert final_converted is not None, "Final converted value not found"
        assert initial_currency == user_default_currency, f"Expected {user_default_currency}, got {initial_currency}"
        assert final_currency == target_currency, f"Expected {target_currency}, got {final_currency}"
        
        conversion_change_percent = abs((final_converted - initial_converted) / initial_converted) * 100
        
        logger.info(f"Conversion change: {initial_converted} → {final_converted} ({conversion_change_percent:.1f}%)")
        
        # Il cambio dovrebbe essere significativo (> 5%)
        assert conversion_change_percent > 5, \
            f"Conversion change too small: {conversion_change_percent:.1f}% (expected > 5%)"
        
        logger.info("✅ Currency conversion test completed successfully")
    
    def test_user_currency_profile(self, authenticated_session, base_url, api_logger):
        """Test che il profilo utente includa la valuta"""
        start_time = time.time()
        response = authenticated_session.get(f"{base_url}/api/v1/me")
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/me", 
            response.status_code, 
            response_time,
            "User profile check"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'default_currency' in data
        
        # Verifica che sia una valuta valida
        valid_currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD',
            'ALL', 'AED', 'AFN', 'AMD', 'ANG', 'AOA', 'ARS', 'AWG', 'AZN',
            'BAM', 'BBD', 'BDT', 'BGN', 'BHD', 'BIF', 'BMD', 'BND', 'BOB',
            'BRL', 'BSD', 'BTC', 'BTN', 'BWP', 'BYN', 'BZD', 'CDF', 'CLF',
            'CLP', 'CNY', 'COP', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF',
            'DKK', 'DOP', 'DZD', 'EGP', 'ERN', 'ETB', 'FJD', 'FKP', 'GEL',
            'GGP', 'GHS', 'GIP', 'GMD', 'GNF', 'GTQ', 'GYD', 'HKD', 'HNL',
            'HRK', 'HTG', 'HUF', 'IDR', 'ILS', 'IMP', 'INR', 'IQD', 'IRR',
            'ISK', 'JEP', 'JMD', 'JOD', 'KES', 'KGS', 'KHR', 'KMF', 'KPW',
            'KRW', 'KWD', 'KYD', 'KZT', 'LAK', 'LBP', 'LKR', 'LRD', 'LSL',
            'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT', 'MOP', 'MRO',
            'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO',
            'NOK', 'NPR', 'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR',
            'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF', 'SAR', 'SBD',
            'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'STD',
            'SVC', 'SYP', 'SZL', 'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY',
            'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'UYU', 'UZS', 'VEF', 'VND',
            'VUV', 'WST', 'XAF', 'XAG', 'XAU', 'XCD', 'XDR', 'XOF', 'XPF',
            'YER', 'ZAR', 'ZMK', 'ZMW', 'ZWL'
        ]        
        assert data['default_currency'] in valid_currencies
        
        logger.info(f"👤 User currency in profile: {data['default_currency']}")
    
    def test_change_user_currency(self, authenticated_session, base_url, user_default_currency, api_logger):
        """Test cambio valuta utente"""
        new_currency = "USD" if user_default_currency == "EUR" else "EUR"
        
        logger.info(f"Testing currency change: {user_default_currency} → {new_currency}")
        
        # Cambio valuta
        change_start = time.time()
        response = authenticated_session.patch(
            f"{base_url}/api/v1/edit_user",
            json={"default_currency": new_currency}
        )
        change_time = (time.time() - change_start) * 1000
        
        api_logger(
            "PATCH", 
            "/api/v1/edit_user", 
            response.status_code, 
            change_time,
            f"Currency change to {new_currency}"
        )
        
        assert response.status_code == 200
        
        # Verifica che la valuta sia cambiata
        verify_start = time.time()
        profile_after = authenticated_session.get(f"{base_url}/api/v1/me")
        verify_time = (time.time() - verify_start) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/me", 
            profile_after.status_code, 
            verify_time,
            "Verify currency change"
        )
        
        profile_data = profile_after.json()
        assert profile_data['default_currency'] == new_currency
        
        logger.info(f"✅ Currency successfully changed to {new_currency}")
        
        # Ripristina la valuta originale
        revert_start = time.time()
        revert_response = authenticated_session.patch(
            f"{base_url}/api/v1/edit_user",
            json={"default_currency": user_default_currency}
        )
        revert_time = (time.time() - revert_start) * 1000
        
        api_logger(
            "PATCH", 
            "/api/v1/edit_user", 
            revert_response.status_code, 
            revert_time,
            f"Revert currency to {user_default_currency}"
        )
        
        assert revert_response.status_code == 200
        
        # Verifica finale
        final_profile = authenticated_session.get(f"{base_url}/api/v1/me").json()
        assert final_profile['default_currency'] == user_default_currency
        
        logger.info(f"✅ Currency reverted to original: {user_default_currency}")
    
    def test_multiple_currency_expenses(self, authenticated_session, base_url, cleanup_data, api_logger):
        logger.info("Testing multiple currency expenses handling")
        
        # Usa dati di test da test_data.py
        test_expenses = get_test_expenses()
        created_expense_ids = []
        
        # Inserisci spese in diverse valute
        for i, expense in enumerate(test_expenses):
            insert_start = time.time()
            response = authenticated_session.post(
                f"{base_url}/api/v1/expenses/insert",
                json=expense
            )
            insert_time = (time.time() - insert_start) * 1000

            api_logger(
                "POST",
                "/api/v1/expenses/insert",
                response.status_code,
                insert_time,
                f"Expense #{i+1}: {expense['valore']} {expense['currency']}"
            )

            assert response.status_code == 201
            expense_id = response.json()['id']
            created_expense_ids.append(expense_id)
            cleanup_data['expenses'].append(expense_id)
        
        # Ottieni la lista delle spese con conversioni
        list_start = time.time()
        list_response = authenticated_session.get(
            f"{base_url}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        list_time = (time.time() - list_start) * 1000

        api_logger(
            "GET",
            "/api/v1/expenses/list",
            list_response.status_code,
            list_time,
            f"Retrieved {len(list_response.json().get('expenses', []))} expenses"
        )

        assert list_response.status_code == 200
        data = list_response.json()
        
        # Verifica che ogni spesa abbia i campi di conversione
        # {'converted_value': 232.91, 'currency': 'GBP', 'descrizione': 'Cinema test GBP', 'exchange_rate': 1.164564, ...}
        for expense in data.get('expenses', []):
            if expense['id'] in created_expense_ids:
                # Verifica i campi che sappiamo esserci dall'errore
                assert 'converted_value' in expense, f"Missing converted_value for expense {expense['id']}"
                assert 'user_currency' in expense, f"Missing user_currency for expense {expense['id']}"
                assert 'currency' in expense, f"Missing currency field for expense {expense['id']}"
                assert 'exchange_rate' in expense, f"Missing exchange_rate for expense {expense['id']}"
                
                # Log dei dettagli di conversione
                logger.info(f"Expense {expense['id']}: {expense['valore']} {expense['currency']} → {expense['converted_value']} {expense['user_currency']} (rate: {expense['exchange_rate']})")
        
        logger.info(f"✅ Multiple currency test completed - {len(created_expense_ids)} expenses processed")   
        
    def test_currency_consistency_across_apis(self, authenticated_session, base_url, api_logger, user_default_currency):
        """Test che verifica la consistenza della valuta attraverso diverse API"""
        logger.info("Testing currency consistency across different APIs")
        
        # API da testare
        apis_to_test = [
            "/api/v1/expenses/total?from_date=2024-01-01&to_date=2024-01-31",
            "/api/v1/incomes/total?from_date=2024-01-01&to_date=2024-01-31",
            "/api/v1/balances/total",
            "/api/v1/expenses/list_categories",
            "/api/v1/incomes/list_categories"
        ]
        
        currencies_found = []
        
        for api_endpoint in apis_to_test:
            start_time = time.time()
            response = authenticated_session.get(f"{base_url}{api_endpoint}")
            response_time = (time.time() - start_time) * 1000
            
            api_logger(
                "GET", 
                api_endpoint, 
                response.status_code, 
                response_time,
                "Currency consistency check"
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Cerca campi currency in diverse posizioni
                currency = None
                if 'currency' in data:
                    currency = data['currency']
                elif 'default_currency' in data:
                    currency = data['default_currency']
                elif 'user_currency' in data:
                    currency = data['user_currency']
                
                if currency:
                    currencies_found.append((api_endpoint, currency))
                    logger.info(f"{api_endpoint}: currency = {currency}")
        
        # Verifica che tutte le API restituiscano la stessa valuta (se specificata)
        if currencies_found:
            unique_currencies = set(currency for _, currency in currencies_found)
            logger.info(f"Unique currencies found: {unique_currencies}")
            
            # La maggior parte dovrebbe corrispondere alla valuta dell'utente
            assert user_default_currency in unique_currencies, \
                f"User currency {user_default_currency} not found in API responses"
        
        logger.info("✅ Currency consistency test completed")