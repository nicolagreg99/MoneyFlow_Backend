import pytest
import time
import logging
from fixtures.test_data import get_test_incomes

logger = logging.getLogger('tests')

class TestIncomesAPI:
    """Test suite per le API delle entrate"""
    
    def test_insert_income(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test inserimento entrata"""
        test_income = get_test_incomes()[0]
        start_time = time.time()
        
        response = authenticated_session.post(
            f"{base_url}/api/v1/incomes/insert",
            json=test_income
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "POST", 
            "/api/v1/incomes/insert", 
            response.status_code, 
            response_time,
            f"Amount: {test_income['valore']} {test_income['currency']}"
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['valore'] == test_income['valore']
        assert data['currency'] == test_income['currency']
        
        # Salva ID per cleanup
        cleanup_data['incomes'].append(data['id'])
        print(f"Income created: ID {data['id']}")
    
    def test_insert_income_multiple_currencies(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test inserimento entrate con diverse valute"""
        test_incomes = get_test_incomes()
        print(f"Testing {len(test_incomes)} incomes with different currencies")
        
        for i, income in enumerate(test_incomes):
            start_time = time.time()
            response = authenticated_session.post(
                f"{base_url}/api/v1/incomes/insert",
                json=income
            )
            response_time = (time.time() - start_time) * 1000
            
            api_logger(
                "POST", 
                "/api/v1/incomes/insert", 
                response.status_code, 
                response_time,
                f"#{i+1}: {income['valore']} {income['currency']}"
            )
            
            assert response.status_code == 201
            data = response.json()
            cleanup_data['incomes'].append(data['id'])
    
    def test_list_incomes(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test lista entrate"""
        # Prima inserisci qualche dato di test
        test_income = get_test_incomes()[0]
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/incomes/insert",
            json=test_income
        )
        income_id = insert_response.json()['id']
        cleanup_data['incomes'].append(income_id)
        
        # Test lista
        start_time = time.time()
        response = authenticated_session.get(
            f"{base_url}/api/v1/incomes/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/incomes/list", 
            response.status_code, 
            response_time,
            f"Found {len(response.json().get('incomes', []))} incomes"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'default_currency' in data
        assert 'incomes' in data
        assert isinstance(data['incomes'], list)
    
    def test_income_totals(self, authenticated_session, base_url, api_logger):
        """Test totali entrate"""
        start_time = time.time()
        response = authenticated_session.get(
            f"{base_url}/api/v1/incomes/total?from_date=2024-01-01&to_date=2024-01-31"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/incomes/total", 
            response.status_code, 
            response_time,
            f"Total: {response.json().get('total', 0)} {response.json().get('currency', 'N/A')}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'currency' in data
        assert isinstance(data['total'], (int, float))
    
    def test_income_categories(self, authenticated_session, base_url, api_logger):
        """Test categorie entrate"""
        start_time = time.time()
        response = authenticated_session.get(f"{base_url}/api/v1/incomes/list_categories")
        response_time = (time.time() - start_time) * 1000
        
        data = response.json()
        api_logger(
            "GET", 
            "/api/v1/incomes/list_categories", 
            response.status_code, 
            response_time,
            f"Categories: {len(data.get('categories', []))}"
        )
        
        assert response.status_code == 200
        assert 'categories' in data
        assert 'default_currency' in data
        assert isinstance(data['categories'], list)
    
    def test_delete_income(self, authenticated_session, base_url, api_logger):
        """Test cancellazione entrata"""
        # Crea entrata da cancellare
        test_income = get_test_incomes()[0]
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/incomes/insert",
            json=test_income
        )
        income_id = insert_response.json()['id']
        print(f"Testing deletion of income ID: {income_id}")
        
        # Cancella
        start_time = time.time()
        delete_response = authenticated_session.delete(
            f"{base_url}/api/v1/incomes/{income_id}"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "DELETE", 
            f"/api/v1/incomes/{income_id}", 
            delete_response.status_code, 
            response_time
        )
        
        assert delete_response.status_code == 200
        print(f"✅ Income {income_id} deleted successfully")
    
    def test_income_currency_conversion(self, authenticated_session, base_url, cleanup_data, user_default_currency, api_logger):
        """Test conversione valuta per le entrate"""
        print(f"Testing income currency conversion - User currency: {user_default_currency}")
        
        # Inserisci un'entrata in valuta diversa
        test_currency = "USD" if user_default_currency == "EUR" else "EUR"
        test_income = {
            "valore": 1000, 
            "tipo": "Test Income", 
            "giorno": "2024-01-15", 
            "currency": test_currency,
            "descrizione": f"Test income conversion {test_currency}->{user_default_currency}"
        }
        
        # Inserimento entrata
        insert_start = time.time()
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/incomes/insert",
            json=test_income
        )
        insert_time = (time.time() - insert_start) * 1000
        api_logger(
            "POST", 
            "/api/v1/incomes/insert", 
            insert_response.status_code, 
            insert_time,
            f"Amount: {test_income['valore']} {test_income['currency']}"
        )
        
        assert insert_response.status_code == 201
        income_id = insert_response.json()['id']
        cleanup_data['incomes'].append(income_id)
        
        # Verifica che l'entrata abbia la conversione
        list_start = time.time()
        list_response = authenticated_session.get(
            f"{base_url}/api/v1/incomes/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        list_time = (time.time() - list_start) * 1000
        api_logger(
            "GET", 
            "/api/v1/incomes/list", 
            list_response.status_code, 
            list_time,
            f"Found {len(list_response.json().get('incomes', []))} incomes"
        )
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Trova l'entrata creata e verifica i campi di conversione
        test_income_data = None
        for income in data.get('incomes', []):
            if income['id'] == income_id:
                test_income_data = income
                break
        
        assert test_income_data is not None, "Test income not found in list"
        assert 'converted_value' in test_income_data, "Missing converted_value"
        assert 'user_currency' in test_income_data, "Missing user_currency"
        assert test_income_data['user_currency'] == user_default_currency
        
        print(f"Income conversion: {test_income_data['valore']} {test_income_data['currency']} → {test_income_data['converted_value']} {test_income_data['user_currency']}")
        
        # Verifica che la conversione sia ragionevole
        assert test_income_data['converted_value'] > 0
        assert test_income_data['converted_value'] != test_income_data['valore']