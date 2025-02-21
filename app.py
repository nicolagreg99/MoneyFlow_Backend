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
from api.entrate.total_incomings_per_day import calcola_totali_giornalieri_entrate 
from api.entrate.delete_income import cancella_entrata
from api.entrate.insert_income import inserisci_entrata
from api.entrate.list_interval_income import incomings_interval
from api.entrate.total_interval_income import incomings_for_period
from api.entrate.total_month_income import totali_mensili_entrate
from api.entrate.total_types_interval_income import total_incomings_by_type_in_range
from api.login.create_user import create_user
from api.login.authenticate_user import authenticate_user
from api.login.reset_password import bp as reset_password_bp
from api.improvements.suggestions import get_suggestions
from api.bilanci.total_month_balances import totali_mensili_bilanci  # Importa la nuova API
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configurazione del logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})

conn = connect_to_database()
cursor = create_cursor(conn)

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

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    response, status_code = create_user(username, email, password)
    
    if status_code == 200:
        user_id = response.get("user_id")
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        response["token"] = token
    
    return jsonify(response), status_code

@app.route('/login', methods=['POST'])
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

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id):
    token = request.headers['x-access-token']
    invalidated_tokens.add(token)
    try:
        return jsonify({'message': 'Successfully logged out!'}), 200
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({'message': 'Logout failed!'}), 500

@app.route('/me', methods=['GET'])
@token_required
def get_user_profile(current_user_id):
    conn = connect_to_database()
    cursor = create_cursor(conn)

    try:
        logger.info(f"Fetching user profile for user_id: {current_user_id}")
        cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (current_user_id,))
        user = cursor.fetchone()
        if user:
            user_info = {
                "id": user[0],
                "username": user[1],
                "email": user[2]
            }
            logger.info(f"User profile data: {user_info}")
            return jsonify(user_info), 200
        else:
            return jsonify({"message": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        return jsonify({"message": "Error retrieving user profile"}), 500
    finally:
        cursor.close()
        conn.close()

# Registrazione del blueprint per il reset della password
app.register_blueprint(reset_password_bp)

# Endpoints per le entrate

@app.route('/entrate/lista_entrate', methods=['GET'])
def get_incomings_interval():
    return incomings_interval()

@app.route('/entrate/totale', methods=['GET'])
@token_required
def get_incomings_for_period(current_user_id):
    return incomings_for_period()

@app.route('/entrate/totale_per_tipo', methods=['GET'])
@token_required
def get_total_incomings_by_type_in_range(current_user_id):
    return total_incomings_by_type_in_range()

@app.route('/totali/giornalieri/entrate', methods=['GET'])
@token_required
def totali_giornalieri(current_user_id):
    return calcola_totali_giornalieri_entrate()

@app.route('/totali/mensili/entrate', methods=['GET'])
@token_required
def totali_entrate_mensili(current_user_id):
    return totali_mensili_entrate()

app.add_url_rule('/entrate/<int:id_guadagno>', methods=['DELETE'], view_func=cancella_entrata)
app.add_url_rule('/entrate', methods=['POST'], view_func=inserisci_entrata)

# Endpoints per le spese

app.add_url_rule('/spese', methods=['POST'], view_func=inserisci_spesa)
app.add_url_rule('/spese/<int:id_spesa>', methods=['DELETE'], view_func=cancella_spesa)

@app.route('/totali/giornalieri/spese', methods=['GET'])
@token_required
def totali_giornalieri_spese(current_user_id):
    return calcola_totali_giornalieri_spese() 

@app.route('/spese/totale', methods=['GET'])
@token_required
def get_expenses_for_period(current_user_id):
    return total_expenses_for_period()

@app.route('/spese/totale_per_tipo', methods=['GET'])
@token_required
def get_total_expenses_by_type_in_range(current_user_id):
    return total_expenses_by_type_in_range()

@app.route('/spese/lista_spese', methods=['GET'])
def get_spese_interval():
    return spese_interval()

@app.route('/totali/mensili/spese', methods=['GET'])
@token_required
def totali_spese_mensili(current_user_id):
    return totali_mensili_spese()

# Endpoints per i bilanci

@app.route('/totali/mensili/bilanci', methods=['GET'])
@token_required
def totali_bilanci_mensili(current_user_id):
    return totali_mensili_bilanci()

# Endpoints per i suggerimenti

@app.route('/suggestions', methods=['GET'])
def suggestions():
    return get_suggestions()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)