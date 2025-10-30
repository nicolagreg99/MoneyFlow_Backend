import requests
import json
import time

# Configurazione
BASE_URL = "http://192.168.1.10:5000"
TEST_USER = {
    "username": "john_doe", 
    "password": "securepassword123"
}

class APITester:
    def __init__(self):
        self.token = None
        self.created_expenses = []
        self.created_incomes = []
        self.session = requests.Session()
    
    def login(self):
        """Effettua il login e ottiene il token"""
        print("Effettuando il login...")
        response = self.session.post(
            f"{BASE_URL}/api/v1/login",
            json=TEST_USER
        )
        
        if response.status_code == 200:
            self.token = response.json()['token']
            print(f"Login riuscito! Token: {self.token[:20]}...")
            self.session.headers.update({'x-access-token': self.token})
            return True
        else:
            print(f"Login fallito: {response.status_code} - {response.text}")
            return False
    
    def test_user_profile(self):
        """Testa il profilo utente"""
        print("\n=== TEST PROFILO UTENTE ===")
        response = self.session.get(f"{BASE_URL}/api/v1/me")
        if response.status_code == 200:
            data = response.json()
            print(f"Profilo utente: {data.get('first_name', 'N/A')} {data.get('last_name', 'N/A')}")
            print(f"Valuta default: {data.get('default_currency', 'N/A')}")
            print(f"Categorie spese: {len(data.get('expenses_categories', []))}")
            print(f"Categorie entrate: {len(data.get('incomes_categories', []))}")
            return True
        else:
            print(f"Errore profilo: {response.status_code} - {response.text}")
            return False
    
    def test_edit_user_currency(self, currency="EUR"):
        """Testa il cambio valuta utente"""
        print(f"\n=== TEST CAMBIO VALUTA A {currency} ===")
        response = self.session.patch(
            f"{BASE_URL}/api/v1/edit_user",
            json={"default_currency": currency}
        )
        if response.status_code == 200:
            print(f"Valuta cambiata a {currency}")
            return True
        else:
            print(f"Errore cambio valuta: {response.status_code} - {response.text}")
            return False
    
    def test_insert_expenses(self):
        """Testa l'inserimento spese con diverse valute"""
        print("\n=== TEST INSERIMENTO SPESE ===")
        
        test_expenses = [
            {"valore": 100, "tipo": "Cibo", "giorno": "2024-01-15", "currency": "USD", "fields": {"descrizione": "Cena test USD"}},
            {"valore": 50, "tipo": "Trasporti", "giorno": "2024-01-16", "currency": "EUR", "fields": {"descrizione": "Treno test EUR"}},
            {"valore": 5000, "tipo": "Shopping", "giorno": "2024-01-17", "currency": "ALL", "fields": {"descrizione": "Shopping test ALL"}},
            {"valore": 75, "tipo": "Intrattenimento", "giorno": "2024-01-18", "fields": {"descrizione": "Cinema test no currency"}}
        ]
        
        for expense in test_expenses:
            response = self.session.post(
                f"{BASE_URL}/api/v1/expenses/insert",
                json=expense
            )
            if response.status_code == 201:
                data = response.json()
                expense_id = data.get('id')
                self.created_expenses.append(expense_id)
                print(f"Spesa inserita: {expense['valore']} {expense.get('currency', 'default')} - ID: {expense_id}")
            else:
                print(f"Errore inserimento spesa: {response.status_code} - {response.text}")
    
    def test_insert_incomes(self):
        """Testa l'inserimento entrate con diverse valute"""
        print("\n=== TEST INSERIMENTO ENTRATE ===")
        
        test_incomes = [
            {"valore": 2000, "tipo": "Stipendio", "giorno": "2024-01-20", "currency": "USD", "descrizione": "Stipendio test USD"},
            {"valore": 1500, "tipo": "Freelance", "giorno": "2024-01-21", "currency": "EUR", "descrizione": "Freelance test EUR"},
            {"valore": 100, "tipo": "Bonus", "giorno": "2024-01-22", "descrizione": "Bonus test no currency"}
        ]
        
        for income in test_incomes:
            response = self.session.post(
                f"{BASE_URL}/api/v1/incomes/insert",
                json=income
            )
            if response.status_code == 201:
                data = response.json()
                income_id = data.get('id')
                if income_id:
                    self.created_incomes.append(income_id)
                    print(f"Entrata inserita: {income['valore']} {income.get('currency', 'default')} - ID: {income_id}")
                else:
                    print(f"ATTENZIONE: Entrata inserita ma ID non restituito - Response: {data}")
            else:
                print(f"Errore inserimento entrata: {response.status_code} - {response.text}")
    
    def test_list_expenses(self):
        """Testa la lista spese"""
        print("\n=== TEST LISTA SPESE ===")
        response = self.session.get(
            f"{BASE_URL}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Valuta utente: {data.get('default_currency')}")
            print(f"Numero spese: {len(data.get('expenses', []))}")
            for expense in data.get('expenses', []):
                print(f"  - {expense['valore']} {expense['currency']} -> {expense.get('converted_value')} {expense.get('user_currency')}")
            return True
        else:
            print(f"Errore lista spese: {response.status_code} - {response.text}")
            return False
    
    def test_list_incomes(self):
        """Testa la lista entrate"""
        print("\n=== TEST LISTA ENTRATE ===")
        response = self.session.get(
            f"{BASE_URL}/api/v1/incomes/list?from_date=2024-01-01&to_date=2024-01-31"
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Valuta utente: {data.get('default_currency')}")
            print(f"Numero entrate: {len(data.get('incomes', []))}")
            for income in data.get('incomes', []):
                print(f"  - {income['valore']} {income['currency']} -> {income.get('converted_value')} {income.get('user_currency')}")
            return True
        else:
            print(f"Errore lista entrate: {response.status_code} - {response.text}")
            return False
    
    def test_totals(self):
        """Testa i totali"""
        print("\n=== TEST TOTALI ===")
        
        # Totali spese
        response = self.session.get(
            f"{BASE_URL}/api/v1/expenses/total?from_date=2024-01-01&to_date=2024-01-31"
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Totale spese: {data.get('total')} {data.get('currency')}")
        
        # Totali entrate
        response = self.session.get(
            f"{BASE_URL}/api/v1/incomes/total?from_date=2024-01-01&to_date=2024-01-31"
        )
        if response.status_code == 200:
            data = response.json()
            print(f"Totale entrate: {data.get('total')} {data.get('currency')}")
    
    def test_categories_endpoints(self):
        """Testa gli endpoint delle categorie"""
        print("\n=== TEST ENDPOINT CATEGORIE ===")
        
        # Categorie spese
        response = self.session.get(f"{BASE_URL}/api/v1/expenses/list_categories")
        if response.status_code == 200:
            data = response.json()
            print(f"Categorie spese: {len(data.get('categories', []))} - Valuta: {data.get('default_currency')}")
        
        # Categorie entrate
        response = self.session.get(f"{BASE_URL}/api/v1/incomes/list_categories")
        if response.status_code == 200:
            data = response.json()
            print(f"Categorie entrate: {len(data.get('categories', []))} - Valuta: {data.get('default_currency')}")
    
    def test_currency_change(self):
        """Testa il cambio valuta e riconversione"""
        print("\n=== TEST CAMBIO VALUTA ===")
        
        # Cambia a EUR
        self.test_edit_user_currency("EUR")
        time.sleep(1)
        self.test_list_expenses()
        
        # Torna a USD
        self.test_edit_user_currency("USD")
        time.sleep(1)
        self.test_list_expenses()
    
    def test_edit_operations(self):
        """Testa la modifica di spese e entrate"""
        print("\n=== TEST MODIFICHE ===")
        
        if self.created_expenses:
            # Modifica una spesa
            expense_id = self.created_expenses[0]
            response = self.session.patch(
                f"{BASE_URL}/api/v1/edit_expense/{expense_id}",
                json={"valore": 150, "currency": "EUR"}
            )
            if response.status_code == 200:
                print(f"Spesa {expense_id} modificata")
        
        if self.created_incomes and self.created_incomes[0]:
            # Modifica un'entrata
            income_id = self.created_incomes[0]
            response = self.session.patch(
                f"{BASE_URL}/api/v1/edit_income/{income_id}",
                json={"valore": 2500, "currency": "EUR"}
            )
            if response.status_code == 200:
                print(f"Entrata {income_id} modificata")
    
    def test_consistency(self):
        """Test di consistenza tra diversi endpoint"""
        print("\n=== TEST CONSISTENZA ===")
        
        # Verifica che i totali siano consistenti
        response_list = self.session.get(f"{BASE_URL}/api/v1/expenses/list?from_date=2024-01-01&to_date=2024-01-31")
        response_total = self.session.get(f"{BASE_URL}/api/v1/expenses/total?from_date=2024-01-01&to_date=2024-01-31")
        
        if response_list.status_code == 200 and response_total.status_code == 200:
            list_data = response_list.json()
            total_data = response_total.json()
            
            # Calcola totale dalla lista
            total_from_list = sum(expense.get('converted_value', 0) for expense in list_data.get('expenses', []))
            total_from_endpoint = total_data.get('total', 0)
            
            print(f"Totale da lista: {round(total_from_list, 2)}")
            print(f"Totale da endpoint: {round(total_from_endpoint, 2)}")
            print(f"Consistente: {abs(total_from_list - total_from_endpoint) < 0.01}")
    
    def test_cleanup(self):
        """Cancella tutte le spese e entrate create dal test"""
        print("\n=== PULIZIA DATI TEST ===")
        
        # Cancella spese
        for expense_id in self.created_expenses:
            response = self.session.delete(f"{BASE_URL}/api/v1/expenses/{expense_id}")
            if response.status_code == 200:
                print(f"Spesa {expense_id} cancellata")
            else:
                print(f"Errore cancellazione spesa {expense_id}: {response.status_code}")
        
        # Cancella entrate (solo quelle con ID valido)
        for income_id in self.created_incomes:
            if income_id:  # Solo se l'ID esiste
                response = self.session.delete(f"{BASE_URL}/api/v1/incomes/{income_id}")
                if response.status_code == 200:
                    print(f"Entrata {income_id} cancellata")
                else:
                    print(f"Errore cancellazione entrata {income_id}: {response.status_code}")
    
    def run_all_tests(self):
        """Esegue tutti i test"""
        print("INIZIO TEST COMPLETO API")
        print("=" * 50)
        
        if not self.login():
            return
        
        try:
            self.test_user_profile()
            self.test_insert_expenses()
            self.test_insert_incomes()
            self.test_list_expenses()
            self.test_list_incomes()
            self.test_totals()
            self.test_categories_endpoints()
            self.test_currency_change()
            self.test_edit_operations()
            self.test_consistency()
            
            print("\n" + "=" * 50)
            print("TEST COMPLETATI")
            
        finally:
            self.test_cleanup()

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()