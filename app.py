import jwt
import datetime
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from database.connection import connect_to_database, create_cursor
from api.spese.insert_expense import inserisci_spesa
from api.spese.delete_expense import cancella_spesa
from api.spese.total_expenses_per_day import calcola_totali_giornalieri_spese 
from api.spese.total_interval_expenses import total_expenses_for_period
from api.spese.total_types_interval_expense import total_expenses_by_type_in_range
from api.spese.list_interval_expenses import spese_interval
from api.spese.total_month_expenses import totali_mensili_spese
from api.spese.list_categories_expenses import list_categories_expenses
from api.entrate.total_incomings_per_day import calcola_totali_giornalieri_entrate 
from api.entrate.delete_income import cancella_entrata
from api.entrate.insert_income import inserisci_entrata
from api.entrate.list_interval_income import incomings_interval
from api.entrate.total_interval_income import incomings_for_period
from api.entrate.total_month_income import totali_mensili_entrate
from api.entrate.total_types_interval_income import total_incomings_by_type_in_range
from api.entrate.list_categories_incomes import list_categories_incomes
from api.users.create_user import create_user
from api.users.edit_user import edit_user
from api.users.authenticate_user import authenticate_user
from api.users.get_user_profile import get_user_profile
from api.users.reset_password import bp as reset_password_bp
from api.improvements.suggestions import get_suggestions
from api.bilanci.total_month_balances import totali_mensili_bilanci
from api.bilanci.total_balances import bilancio_totale
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return jsonify({'message': 'Failed to authenticate token.'}), 500

        return f(current_user_id, *args, **kwargs)
    return decorated

@app.route('/api/v1/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    expenses = data.get('expenses', [])
    incomes = data.get('incomes', [])

    response, status_code = create_user(username, email, password, first_name, last_name, expenses, incomes)
    
    if status_code == 200:
        user_id = response.get("user_id")
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        response["token"] = token
    
    return jsonify(response), status_code


@app.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = authenticate_user(username, password)
    if user:
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token}), 200
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

invalidated_tokens = set()

@app.route('/api/v1/logout', methods=['POST'])
@token_required
def logout(current_user_id):
    token = request.headers['x-access-token']
    invalidated_tokens.add(token)
    try:
        return jsonify({'message': 'Successfully logged out!'}), 200
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({'message': 'Logout failed!'}), 500

@app.route('/api/v1/me', methods=['GET'])
@token_required
def me(current_user_id):
    return get_user_profile(current_user_id)

# Registrazione del blueprint per il reset della password
app.register_blueprint(reset_password_bp)

@app.route("/api/v1/edit_user", methods=["PUT"])
@token_required
def edit_user_api(user_id):
    return edit_user(user_id)

# Endpoints per le entrate

@app.route('/api/v1/entrate/lista_entrate', methods=['GET'])
@token_required
def get_incomings_interval(current_user_id):
    return incomings_interval(current_user_id)

@app.route('/api/v1/entrate/totale', methods=['GET'])
@token_required
def get_incomings_for_period(current_user_id):
    return incomings_for_period()

@app.route('/api/v1/entrate/totale_per_tipo', methods=['GET'])
@token_required
def get_total_incomings_by_type_in_range(current_user_id):
    return total_incomings_by_type_in_range()

@app.route('/api/v1/totali/giornalieri/entrate', methods=['GET'])
@token_required
def totali_giornalieri(current_user_id):
    return calcola_totali_giornalieri_entrate()

@app.route('/api/v1/totali/mensili/entrate', methods=['GET'])
@token_required
def totali_entrate_mensili(current_user_id):
    return totali_mensili_entrate()

app.add_url_rule('/api/v1/entrate/<int:id_guadagno>', methods=['DELETE'], view_func=cancella_entrata)

@app.route('/api/v1/entrate', methods=['POST'])
@token_required
def inserisci_entrata_api(user_id):
    return inserisci_entrata(user_id)

@app.route('/api/v1/entrate/list_categories', methods=['GET'])
@token_required
def get_incomes_categories(user_id):
    """API to get incomes categories"""
    return list_categories_incomes(user_id)

# Endpoints per le spese

@app.route('/api/v1/spese', methods=['POST'])
@token_required
def inserisci_spesa_api(user_id):
    return inserisci_spesa(user_id)

app.add_url_rule('/api/v1/spese/<int:id_spesa>', methods=['DELETE'], view_func=cancella_spesa)

@app.route('/api/v1/totali/giornalieri/spese', methods=['GET'])
@token_required
def totali_giornalieri_spese(current_user_id):
    return calcola_totali_giornalieri_spese() 

@app.route('/api/v1/spese/totale', methods=['GET'])
@token_required
def get_expenses_for_period(current_user_id):
    return total_expenses_for_period()

@app.route('/api/v1/spese/totale_per_tipo', methods=['GET'])
@token_required
def get_total_expenses_by_type_in_range(current_user_id):
    return total_expenses_by_type_in_range()

@app.route('/api/v1/spese/lista_spese', methods=['GET'])
@token_required
def get_spese_interval(current_user_id):
    return spese_interval(current_user_id)

@app.route('/api/v1/totali/mensili/spese', methods=['GET'])
@token_required
def totali_spese_mensili(current_user_id):
    return totali_mensili_spese()

@app.route("/api/v1/spese/list_categories", methods=["GET"])
@token_required
def list_categories_expenses_api(user_id):
    return list_categories_expenses(user_id)

# Endpoints per i bilanci

@app.route('/api/v1/bilancio/totale', methods=['GET'])
def get_bilancio_totale():
    return bilancio_totale()

@app.route('/api/v1/totali/mensili/bilanci', methods=['GET'])
@token_required
def totali_bilanci_mensili(current_user_id):
    return totali_mensili_bilanci()

# Endpoints per i suggerimenti

@app.route('/api/v1/suggestions', methods=['GET'])
def suggestions():
    return get_suggestions()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)