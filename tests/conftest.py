import pytest
import requests
import os
import sys
import time
import logging
from datetime import datetime

# Aggiungi la root del progetto al path Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.config import get_environment_config, REQUEST_TIMEOUT

# Setup logging per i test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='H:%M:%S'
)
logger = logging.getLogger('tests')

# Variabile globale per tracciare tutte le chiamate API
API_CALLS = []
# Variabile per memorizzare la currency originale dell'utente
ORIGINAL_USER_CURRENCY = None

@pytest.fixture(scope="session", autouse=True)
def print_final_report():
    """Stampa un report finale di tutte le API testate"""
    yield
    
    # Stampare il report solo se ci sono chiamate API registrate
    if API_CALLS:
        print("\n" + "="*80)
        print("🎯 FINAL API TEST REPORT")
        print("="*80)
        
        # Statistiche generali
        total_calls = len(API_CALLS)
        successful_calls = len([call for call in API_CALLS if call['status'] < 400])
        failed_calls = total_calls - successful_calls
        avg_time = sum(call['time'] for call in API_CALLS) / total_calls
        
        print(f"📊 Total API Calls: {total_calls}")
        print(f"✅ Successful: {successful_calls}")
        print(f"❌ Failed: {failed_calls}")
        print(f"⏱️  Average Response Time: {avg_time:.1f}ms")
        print("-" * 80)
        
        # Dettaglio per endpoint
        endpoints = {}
        for call in API_CALLS:
            endpoint = call['endpoint']
            if endpoint not in endpoints:
                endpoints[endpoint] = []
            endpoints[endpoint].append(call)
        
        for endpoint, calls in sorted(endpoints.items()):
            success_count = len([c for c in calls if c['status'] < 400])
            fail_count = len(calls) - success_count
            avg_endpoint_time = sum(c['time'] for c in calls) / len(calls)
            status = "✅" if fail_count == 0 else "⚠️ " if success_count > 0 else "❌"
            
            print(f"{status} {endpoint:45s} Calls: {len(calls):2d} | Success: {success_count:2d} | Fail: {fail_count:2d} | Avg Time: {avg_endpoint_time:6.1f}ms")
        
        print("="*80)

@pytest.fixture(scope="session")
def base_url():
    """Restituisce l'URL base dell'applicazione"""
    config = get_environment_config()
    url = config['base_url']
    logger.info(f"🎯 Test environment: {url}")
    return url

@pytest.fixture(scope="session")
def test_user():
    """Credenziali di test"""
    config = get_environment_config()
    user_data = {
        "username": config['username'],
        "password": config['password']
    }
    logger.info(f"👤 Test user: {user_data['username']}")
    return user_data

@pytest.fixture(scope="session")
def authenticated_session(base_url, test_user):
    """Crea una sessione autenticata per l'intera sessione di test"""
    session = requests.Session()
    
    try:
        # Login una sola volta per tutta la sessione
        login_start = time.time()
        response = session.post(
            f"{base_url}/api/v1/login",
            json=test_user,
            timeout=REQUEST_TIMEOUT
        )
        login_time = (time.time() - login_start) * 1000
        
        if response.status_code == 200:
            token = response.json()['token']
            session.headers.update({'x-access-token': token})
            
            # Registra la chiamata di login
            API_CALLS.append({
                'method': 'POST',
                'endpoint': '/api/v1/login',
                'status': response.status_code,
                'time': login_time,
                'info': f"User: {test_user['username']}"
            })
            
            print(f"✅ POST   /api/v1/login{' ' * 33} {response.status_code:3d} 🟢 {login_time:6.1f}ms - User: {test_user['username']}")
            
            # Ottieni la currency originale una sola volta
            global ORIGINAL_USER_CURRENCY
            profile_start = time.time()
            profile_response = session.get(f"{base_url}/api/v1/me")
            profile_time = (time.time() - profile_start) * 1000
            
            if profile_response.status_code == 200:
                ORIGINAL_USER_CURRENCY = profile_response.json().get('default_currency', 'EUR')
                print(f"Original user currency saved: {ORIGINAL_USER_CURRENCY}")
                
                API_CALLS.append({
                    'method': 'GET',
                    'endpoint': '/api/v1/me',
                    'status': profile_response.status_code,
                    'time': profile_time,
                    'info': 'Get original user currency'
                })
            
            yield session
            
            # RIPRISTINO FINALE della currency originale
            if ORIGINAL_USER_CURRENCY:
                restore_start = time.time()
                restore_response = session.patch(
                    f"{base_url}/api/v1/edit_user",
                    json={"default_currency": ORIGINAL_USER_CURRENCY}
                )
                restore_time = (time.time() - restore_start) * 1000
                
                if restore_response.status_code == 200:
                    print(f"FINAL RESTORE: Currency reset to {ORIGINAL_USER_CURRENCY} 🟢 {restore_time:.1f}ms")
                else:
                    print(f"⚠️  Failed to restore currency: {restore_response.status_code}")
                
                API_CALLS.append({
                    'method': 'PATCH',
                    'endpoint': '/api/v1/edit_user',
                    'status': restore_response.status_code,
                    'time': restore_time,
                    'info': f"Final restore currency to {ORIGINAL_USER_CURRENCY}"
                })
            
        else:
            print(f"❌ POST   /api/v1/login{' ' * 33} {response.status_code:3d} 🔴 {login_time:6.1f}ms")
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error to {base_url}: {e}")
        pytest.skip(f"Cannot connect to {base_url}: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout connecting to {base_url}: {e}")
        pytest.skip(f"Timeout connecting to {base_url}: {e}")
    except Exception as e:
        print(f"Unexpected error during authentication: {e}")
        pytest.skip(f"Unexpected error: {e}")
    finally:
        session.close()
        print("Session closed")

@pytest.fixture(scope="function")
def user_default_currency(authenticated_session, base_url):
    """Ottiene la valuta di default dell'utente"""
    start_time = time.time()
    response = authenticated_session.get(f"{base_url}/api/v1/me")
    
    if response.status_code == 200:
        data = response.json()
        currency = data.get('default_currency', 'EUR')
        elapsed = (time.time() - start_time) * 1000
        
        # Registra la chiamata API
        API_CALLS.append({
            'method': 'GET',
            'endpoint': '/api/v1/me',
            'status': response.status_code,
            'time': elapsed,
            'info': 'Get user currency'
        })
        
        print(f"✅ GET    /api/v1/me{' ' * 36} {response.status_code:3d} 🟢 {elapsed:6.1f}ms - Currency: {currency}")
        return currency
    else:
        print(f"❌ GET    /api/v1/me{' ' * 36} {response.status_code:3d} 🔴 {(time.time()-start_time)*1000:6.1f}ms")
        pytest.skip(f"Cannot get user profile: {response.status_code}")

@pytest.fixture(scope="function")
def cleanup_data(authenticated_session, base_url):
    """Fixture per pulire i dati dopo ogni test"""
    created_ids = {
        'expenses': [],
        'incomes': []
    }
    
    yield created_ids
    
    # PULIZIA COMPLETA dopo il test
    deleted_count = 0
    
    # Cancella spese create
    for expense_id in created_ids['expenses']:
        try:
            delete_start = time.time()
            response = authenticated_session.delete(f"{base_url}/api/v1/expenses/{expense_id}")
            delete_time = (time.time() - delete_start) * 1000
            
            if response.status_code == 200:
                deleted_count += 1
                print(f"Deleted expense {expense_id} 🟢 {delete_time:.1f}ms")
            else:
                print(f"⚠️  Failed to delete expense {expense_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error deleting expense {expense_id}: {e}")
    
    # Cancella entrate create
    for income_id in created_ids['incomes']:
        try:
            delete_start = time.time()
            response = authenticated_session.delete(f"{base_url}/api/v1/incomes/{income_id}")
            delete_time = (time.time() - delete_start) * 1000
            
            if response.status_code == 200:
                deleted_count += 1
                print(f"Deleted income {income_id} 🟢 {delete_time:.1f}ms")
            else:
                print(f"⚠️  Failed to delete income {income_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error deleting income {income_id}: {e}")
    
    if deleted_count > 0:
        print(f"Cleanup completed: {deleted_count} items deleted")

@pytest.fixture(scope="function")
def api_logger():
    """Logger per tracciare le chiamate API con output diretto in console"""
    def log_api_call(method, endpoint, status_code, response_time, additional_info=""):
        # Determina l'emoji in base al tempo di risposta
        if response_time < 100:
            time_emoji = "🟢"
        elif response_time < 500:
            time_emoji = "🟡"
        else:
            time_emoji = "🔴"
        
        # Determina l'emoji in base allo status code
        status_emoji = "✅" if status_code < 400 else "❌"
        
        # Formatta l'output
        method_str = f"{method:5s}"
        endpoint_str = f"{endpoint:40s}"
        status_str = f"{status_code:3d}"
        time_str = f"{response_time:6.1f}ms"
        
        # Costruisci il messaggio
        message = f"{status_emoji} {method_str} {endpoint_str} {status_str} {time_emoji} {time_str}"
        if additional_info:
            message += f" - {additional_info}"
        
        # Stampa direttamente in console
        print(message)
        
        # Registra anche nella lista globale per il report finale
        API_CALLS.append({
            'method': method,
            'endpoint': endpoint,
            'status': status_code,
            'time': response_time,
            'info': additional_info
        })
    
    return log_api_call