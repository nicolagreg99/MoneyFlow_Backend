import pytest
import time
import logging
from fixtures.test_data import get_test_expenses

logger = logging.getLogger('tests')

class TestExpensesAPI:
    """Test suite per le API delle spese"""
    
    def test_insert_expense(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test inserimento spesa"""
        test_expense = get_test_expenses()[0]
        start_time = time.time()
        
        response = authenticated_session.post(
            f"{base_url}/api/v1/expenses/insert",
            json=test_expense
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "POST", 
            "/api/v1/expenses/insert", 
            response.status_code, 
            response_time,
            f"Amount: {test_expense['valore']} {test_expense['currency']}"
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['valore'] == test_expense['valore']
        assert data['currency'] == test_expense['currency']
        
        # Salva ID per cleanup
        cleanup_data['expenses'].append(data['id'])
        logger.info(f"Expense created: ID {data['id']}")
    
    def test_insert_expense_multiple_currencies(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test inserimento spese con diverse valute"""
        test_expenses = get_test_expenses()
        logger.info(f"Testing {len(test_expenses)} expenses with different currencies")
        
        for i, expense in enumerate(test_expenses):
            start_time = time.time()
            response = authenticated_session.post(
                f"{base_url}/api/v1/expenses/insert",
                json=expense
            )
            response_time = (time.time() - start_time) * 1000
            
            api_logger(
                "POST", 
                "/api/v1/expenses/insert", 
                response.status_code, 
                response_time,
                f"#{i+1}: {expense['valore']} {expense['currency']}"
            )
            
            assert response.status_code == 201
            data = response.json()
            cleanup_data['expenses'].append(data['id'])
    
    def test_list_expenses(self, authenticated_session, base_url, cleanup_data, api_logger):
        """Test lista spese"""
        # Prima inserisci qualche dato di test
        test_expense = get_test_expenses()[0]
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/expenses/insert",
            json=test_expense
        )
        expense_id = insert_response.json()['id']
        cleanup_data['expenses'].append(expense_id)
        
        # Test lista
        start_time = time.time()
        response = authenticated_session.get(
            f"{base_url}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/expenses/list", 
            response.status_code, 
            response_time,
            f"Found {len(response.json().get('expenses', []))} expenses"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'default_currency' in data
        assert 'expenses' in data
        assert isinstance(data['expenses'], list)
    
    def test_expense_totals(self, authenticated_session, base_url, api_logger):
        """Test totali spese"""
        start_time = time.time()
        response = authenticated_session.get(
            f"{base_url}/api/v1/expenses/total?from_date=2024-01-01&to_date=2024-01-31"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "GET", 
            "/api/v1/expenses/total", 
            response.status_code, 
            response_time,
            f"Total: {response.json().get('total', 0)} {response.json().get('currency', 'N/A')}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total' in data
        assert 'currency' in data
        assert isinstance(data['total'], (int, float))
    
    def test_expense_categories(self, authenticated_session, base_url, api_logger):
        """Test categorie spese"""
        start_time = time.time()
        response = authenticated_session.get(f"{base_url}/api/v1/expenses/list_categories")
        response_time = (time.time() - start_time) * 1000
        
        data = response.json()
        api_logger(
            "GET", 
            "/api/v1/expenses/list_categories", 
            response.status_code, 
            response_time,
            f"Categories: {len(data.get('categories', []))}"
        )
        
        assert response.status_code == 200
        assert 'categories' in data
        assert 'default_currency' in data
        assert isinstance(data['categories'], list)
    
    def test_delete_expense(self, authenticated_session, base_url, api_logger):
        """Test cancellazione spesa"""
        # Crea spesa da cancellare
        test_expense = get_test_expenses()[0]
        insert_response = authenticated_session.post(
            f"{base_url}/api/v1/expenses/insert",
            json=test_expense
        )
        expense_id = insert_response.json()['id']
        logger.info(f"Testing deletion of expense ID: {expense_id}")
        
        # Cancella
        start_time = time.time()
        delete_response = authenticated_session.delete(
            f"{base_url}/api/v1/expenses/{expense_id}"
        )
        response_time = (time.time() - start_time) * 1000
        
        api_logger(
            "DELETE", 
            f"/api/v1/expenses/{expense_id}", 
            delete_response.status_code, 
            response_time
        )
        
        assert delete_response.status_code == 200
        logger.info(f"✅ Expense {expense_id} deleted successfully")