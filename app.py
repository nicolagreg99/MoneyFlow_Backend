import jwt
import datetime
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from database.connection import connect_to_database, create_cursor
from api.insert_expense import inserisci_spesa
from api.delete_expense import cancella_spesa
from api.total_week_expense import totali_settimanali # totale settimanale
from api.total_types_week_expense import totali_settimanali_per_tipo # totale settimanale per tipo di spesa
from api.total_types_month_expense import calcola_totali_mensili_per_tipo
from api.total_month_expense import totali_mensili
from api.create_user import create_user
from api.authenticate_user import authenticate_user
from api.list_week_expenses import spese_settimanali # lista delle spese settimanali
from api.list_month_expenses import spese_mensili
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

@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user_id):
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

@app.route('/spese/settimanali', methods=['GET'])
def get_spese_settimanali():
    return spese_settimanali()

@app.route('/spese/mensili', methods=['GET'])
def get_spese_mensili():
    return spese_mensili()

@app.route('/totale_mensile', methods=['GET'])
def get_totale_mensile():
    return totali_mensili()

@app.route('/totali/mensili_per_tipo', methods=['GET'])
def totali_mensili_per_tipo():
    return calcola_totali_mensili_per_tipo()

# Endpoint per l'inserimento e l'eliminazione delle spese
app.add_url_rule('/spese', methods=['POST'], view_func=inserisci_spesa)
app.add_url_rule('/spese/<int:id_spesa>', methods=['DELETE'], view_func=cancella_spesa)
app.add_url_rule('/totale_settimanale', methods=['GET'], view_func=totali_settimanali)
app.add_url_rule('/totali/settimanali_per_tipo', methods=['GET'], view_func=totali_settimanali_per_tipo)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

