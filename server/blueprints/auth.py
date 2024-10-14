from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Tutti i campi sono obbligatori"}), 400
    
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, generate_password_hash(password)))
    db.connection.commit()
    cursor.close()

    # Registrazione qui
    return jsonify({"message": "Registrazione avvenuta con successo"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Tutti i campi sono obbligatori"}), 400

    # Autenticazione qui
    return jsonify({"message": "Login avvenuto con successo"}), 200

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "L'email è obbligatoria"}), 400

    # Reset password qui
    return jsonify({"message": "Istruzioni per il recupero della password inviate"}), 200