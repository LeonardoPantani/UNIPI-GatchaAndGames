import connexion
import uuid
import bcrypt
import requests
import json
from datetime import datetime

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
auth_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


@auth_circuit_breaker
def login():
    if 'username' in session:
        return jsonify({"error": "You are already logged in"}), 409
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request"}), 400
    
    # richiesta json valida
    login_request = connexion.request.get_json()
    username_to_login = login_request.get("username")
    password_to_login = login_request.get("password")

    try:
        payload = { "username": username_to_login }
        url = "http://db_manager:8080/db_manager/auth/login"
        response = requests.post(url, json=payload)
        data = response.json()

        if response.status_code == 404: # user not found (we do not show that to the user)
            return jsonify({"error": "Invalid credentials."}), 201
        
        if response.status_code != 200: # for other error codes we return 500
            return jsonify({"error": "Service unavailable."}), 503

        if bcrypt.checkpw(password_to_login.encode('utf-8'), data["password"].encode('utf-8')):
            session['uuid'] = data["uuid"]
            session['uuid_hex'] = data["uuid_hex"]
            session['email'] = data["email"]
            session['username'] = data["username"]
            session['role'] = data["role"]
            session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid credentials."}), 401
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except ValueError:
        return jsonify({"error": "Service unavailable."}), 503
 

@auth_circuit_breaker
def logout():   
    # Check if user is logged in
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    # Remove session cookie to log out
    response = make_response(jsonify({"message": "Logout successful"}), 200)
    session.clear()
    return response


@auth_circuit_breaker
def register():
    if 'username' in session:
        return jsonify({"error": "You are already logged in"}), 409
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request"}), 400
    
    # richiesta json valida
    register_request = connexion.request.get_json()
    username_to_register = register_request.get("username")
    email_to_register = register_request.get("email")
    password_to_hash = register_request.get("password")

    if not username_to_register or not email_to_register or not password_to_hash:
        return jsonify({"error": "Missing required fields"}), 400

    # hashing
    password_hashed = bcrypt.hashpw(password_to_hash.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # generating UUID
    uuid_hex_to_register = uuid.uuid4().bytes
    uuid_to_register = str(uuid.UUID(bytes=uuid_hex_to_register))

    try:
        payload = { "uuid": uuid_to_register, "username": username_to_register, "email": email_to_register, "password": password_hashed }
        url = "http://db_manager:8080/db_manager/auth/register"
        response = requests.post(url, json=payload)

        if response.status_code == 409: # email provided already in use
            return jsonify(response.json()), response.status_code
        
        if response.status_code != 201: # for other error codes we return 503
            return jsonify({"error": "Service unavailable."}), 503

        # visto che vogliamo che l'utente si auto-logghi quando si registra controlliamo che la registrazione abbia successo qui
        session['uuid'] = uuid_to_register
        session['uuid_hex'] = uuid_hex_to_register
        session['email'] = email_to_register
        session['username'] = username_to_register
        session['role'] = "USER"
        session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({"message": "Registration successful."}), 201
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503