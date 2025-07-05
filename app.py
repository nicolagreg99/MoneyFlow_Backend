import jwt
import datetime
import logging
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import API modules
from api.v1.expenses.insert_expense import insert_expense
from api.v1.expenses.delete_expense import delete_expense
from api.v1.expenses.edit_expense import edit_expense
from api.v1.expenses.total_expenses_per_day import total_expenses_by_day
from api.v1.expenses.total_interval_expenses import total_expenses
from api.v1.expenses.total_types_interval_expense import total_expenses_by_category
from api.v1.expenses.list_interval_expenses import expenses_list
from api.v1.expenses.total_month_expenses import total_expenses_by_month
from api.v1.expenses.list_categories_expenses import list_categories_expenses

from api.v1.incomes.insert_income import insert_income
from api.v1.incomes.delete_income import delete_income
from api.v1.incomes.edit_income import edit_income
from api.v1.incomes.list_interval_income import incomes_list
from api.v1.incomes.total_incomings_per_day import total_incomes_by_day
from api.v1.incomes.total_interval_income import total_incomes
from api.v1.incomes.total_types_interval_income import total_incomes_by_category
from api.v1.incomes.total_month_income import total_incomes_by_month
from api.v1.incomes.list_categories_incomes import list_categories_incomes

from api.v1.users.create_user import create_user
from api.v1.users.edit_user import edit_user
from api.v1.users.authenticate_user import authenticate_user
from api.v1.users.get_user_profile import get_user_profile
from api.v1.users.reset_password import bp as reset_password_bp

from api.v1.balances.total_month_balances import total_balances_by_month
from api.v1.balances.total_balances import total_balance


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

## USER -----------------------------------------------------------

# Token creation
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

# User registration
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

# User login
@app.route('/api/v1/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ip_address = request.remote_addr

    logger.info(f"Tentativo di login da IP: {ip_address} - Username: {username}")

    user = authenticate_user(username, password)

    if user:
        logger.info(f"Login riuscito per l'utente: {username}")
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token}), 200
    else:
        if username:
            logger.warning(f"Login fallito per l'utente: {username} - Password errata o utente non esistente.")
        else:
            logger.warning(f"Login fallito: username non fornito.")
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

invalidated_tokens = set()

# User logout
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

# User profile
@app.route('/api/v1/me', methods=['GET'])
@token_required
def me(user_id):
    return get_user_profile(user_id)

# Reset password
app.register_blueprint(reset_password_bp)

# Edit user
@app.route("/api/v1/edit_user", methods=["PATCH"])
@token_required
def edit_user_api(user_id):
    return edit_user(user_id)

## INCOMES -----------------------------------------------------------

# Income list
@app.route('/api/v1/incomes/list', methods=['GET'])
@token_required
def incomes_list_api(user_id):
    return incomes_list(user_id)

# Total incomes 
@app.route('/api/v1/incomes/total', methods=['GET'])
@token_required
def total_incomes_api(user_id):
    return total_incomes()

# Income total group by category
@app.route('/api/v1/incomes/total_by_category', methods=['GET'])
@token_required
def total_incomes_by_category_api(user_id):
    return total_incomes_by_category()

# Income total group by day
@app.route('/api/v1/incomes/total_by_day', methods=['GET'])
@token_required
def total_incomes_by_day_api(user_id):
    return total_incomes_by_day()

# Income total group by month
@app.route('/api/v1/incomes/total_by_month', methods=['GET'])
@token_required
def total_incomes_by_month_api(user_id):
    return total_incomes_by_month()

# Delete income
@app.route('/api/v1/incomes/<int:id_entrata>', methods=['DELETE'])
@token_required
def delete_income_api(user_id, id_entrata):
    return delete_income(id_entrata)

# Edit income
@app.route("/api/v1/edit_income/<int:id_entrata>", methods=["PATCH"])
@token_required
def edit_income_api(user_id, id_entrata):
    return edit_income(id_entrata, user_id)

# Insert income
@app.route('/api/v1/incomes/insert', methods=['POST'])
@token_required
def insert_income_api(user_id):
    return insert_income(user_id)

# Show list income category
@app.route('/api/v1/incomes/list_categories', methods=['GET'])
@token_required
def list_categories_incomes_api(user_id):
    """API to get incomes categories"""
    return list_categories_incomes(user_id)

## EXPENSES -----------------------------------------------------------

# Insert expense
@app.route('/api/v1/expenses/insert', methods=['POST'])
@token_required
def insert_expense_api(user_id):
    return insert_expense(user_id)

# Delete expense
@app.route('/api/v1/expenses/<int:id_spesa>', methods=['DELETE'])
@token_required
def delete_expense_api(user_id, id_spesa):
    return delete_expense(id_spesa)

# Edit expense
@app.route("/api/v1/edit_expense/<int:id_spesa>", methods=["PATCH"])
@token_required
def edit_expense_api(user_id, id_spesa):
    return edit_expense(id_spesa, user_id)

# Expense total group by day
@app.route('/api/v1/expenses/total_by_day', methods=['GET'])
@token_required
def total_expenses_by_day_api(user_id):
    return total_expenses_by_day() 

# Total expenses
@app.route('/api/v1/expenses/total', methods=['GET'])
@token_required
def total_expenses_api(user_id):
    return total_expenses()

# Expense total group by category
@app.route('/api/v1/expenses/total_by_category', methods=['GET'])
@token_required
def total_expenses_by_category_api(user_id):
    return total_expenses_by_category()

# Expense list
@app.route('/api/v1/expenses/list', methods=['GET'])
@token_required
def expenses_list_api(user_id):
    return expenses_list(user_id)

# Expense total group by month
@app.route('/api/v1/expenses/total_by_month', methods=['GET'])
@token_required
def total_expenses_by_month_api(user_id):
    return total_expenses_by_month()

# Show list expense category
@app.route("/api/v1/expenses/list_categories", methods=["GET"])
@token_required
def list_categories_expenses_api(user_id):
    return list_categories_expenses(user_id)

## BALANCES --------------------------------------------------------

# Total balances
@app.route('/api/v1/balances/total', methods=['GET'])
def total_balance_api():
    return total_balance()

# Total balances group by month
@app.route('/api/v1/balances/total_by_month', methods=['GET'])
@token_required
def total_balances_by_month_api(user_id):
    return total_balances_by_month(user_id)