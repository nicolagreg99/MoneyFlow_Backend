"""
Configurazione per i test
"""
import os

# Configurazioni per diversi ambienti
ENVIRONMENTS = {
    'local': {
        'base_url': 'http://localhost:5000',
        'username': 'nicola', 
        'password': 'test'
    },
    'development': {
        'base_url': 'http://dev-server:5000',
        'username': 'test_user',
        'password': 'test_pass'
    },
    'staging': {
        'base_url': 'https://staging.example.com',
        'username': os.environ.get('STAGING_USER'),
        'password': os.environ.get('STAGING_PASS')
    }
}

# Timeout for the requests
REQUEST_TIMEOUT = 30

def get_environment_config(env=None):
    """Restituisce la configurazione per l'ambiente specificato"""
    env = env or os.environ.get('TEST_ENV', 'local')
    return ENVIRONMENTS.get(env, ENVIRONMENTS['local'])

config = get_environment_config()
TEST_BASE_URL = config['base_url']
TEST_USERNAME = config['username']
TEST_PASSWORD = config['password']