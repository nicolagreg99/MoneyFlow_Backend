import requests

# URL del server Flask
BASE_URL = 'http://127.0.0.1:5000'

def test_register():
    url = f"{BASE_URL}/register"
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    }
    response = requests.post(url, json=data)
    return response.json()

def test_login():
    url = f"{BASE_URL}/login"
    data = {
        "username": "Venada",
        "password": "aaaa"
    }
    response = requests.post(url, json=data)
    return response.json()

def test_get_user_profile(token):
    url = f"{BASE_URL}/me"
    headers = {
        "x-access-token": token
    }
    response = requests.get(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    # Step 1: Register a new user
    print("Registering new user...")
    register_response = test_register()
    print(register_response)
    
    # Step 2: Log in to get the JWT token
    print("Logging in...")
    login_response = test_login()
    print(login_response)
    
    token = login_response.get('token')
    if token:
        # Step 3: Access the user profile using the JWT token
        print("Getting user profile...")
        profile_response = test_get_user_profile(token)
        print(profile_response)
    else:
        print("Login failed, cannot get token.")
