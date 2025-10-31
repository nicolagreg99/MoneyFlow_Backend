"""
Dati di test centralizzati
"""
def get_test_expenses():
    """Restituisce dati di test per le spese"""
    return [
        {
            "valore": 100, 
            "tipo": "Cibo", 
            "giorno": "2024-01-15", 
            "currency": "USD", 
            "fields": {"descrizione": "Cena test USD"}
        },
        {
            "valore": 50, 
            "tipo": "Trasporti", 
            "giorno": "2024-01-16", 
            "currency": "EUR", 
            "fields": {"descrizione": "Treno test EUR"}
        },
        {
            "valore": 200, 
            "tipo": "Intrattenimento", 
            "giorno": "2024-01-17", 
            "currency": "GBP", 
            "fields": {"descrizione": "Cinema test GBP"}
        }
    ]

def get_test_incomes():
    """Restituisce dati di test per le entrate"""
    return [
        {
            "valore": 2000, 
            "tipo": "Stipendio", 
            "giorno": "2024-01-20", 
            "currency": "USD", 
            "descrizione": "Stipendio test USD"
        },
        {
            "valore": 1500, 
            "tipo": "Freelance", 
            "giorno": "2024-01-21", 
            "currency": "EUR", 
            "descrizione": "Freelance test EUR"
        },
        {
            "valore": 800, 
            "tipo": "Investimenti", 
            "giorno": "2024-01-22", 
            "currency": "CHF", 
            "descrizione": "Dividendi test CHF"
        }
    ]

def get_currency_test_cases():
    return [
        {"from": "USD", "to": "EUR", "amount": 100},
        {"from": "EUR", "to": "USD", "amount": 50},
        {"from": "USD", "to": "ALL", "amount": 200},
    ]

def get_test_user_data():
    """Dati per test di registrazione utente"""
    return {
        "username": "test_user_" + str(hash(str(__import__('time').time())))[-6:],
        "email": f"test_{str(hash(str(__import__('time').time())))[-6:]}@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "currency": "EUR"
    }