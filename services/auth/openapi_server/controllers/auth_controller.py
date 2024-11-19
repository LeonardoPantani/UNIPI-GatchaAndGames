import connexion
import uuid
import bcrypt
import requests
import json
import logging
from datetime import datetime

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest
from openapi_server import util
import logging

from flask import current_app, jsonify, request, session

from pybreaker import CircuitBreaker, CircuitBreakerListener, CircuitBreakerError

# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])


def health_check():
    return jsonify({"message": "Service operational."}), 200


def login():
    if 'username' in session:
        return jsonify({"error": "You are already logged in."}), 409
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    # valid json request
    login_request = connexion.request.get_json()
    username_to_login = login_request.get("username")
    password_to_login = login_request.get("password")

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = { "username": username_to_login }
            url = "http://db_manager:8080/db_manager/auth/login"
            response = requests.post(url, json=payload)
            response.raise_for_status() # if response is obtained correctly 
            return response.json()

        response_data = make_request_to_dbmanager()

        if bcrypt.checkpw(password_to_login.encode('utf-8'), response_data["password"].encode('utf-8')): # wrong password
            session['uuid'] = response_data["uuid"]
            session['uuid_hex'] = response_data["uuid_hex"]
            session['email'] = response_data["email"]
            session['username'] = response_data["username"]
            session['role'] = response_data["role"]
            session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return jsonify({"message": "Login successful."}), 200
        else:
            return jsonify({"error": "Invalid credentials."}), 401

    except requests.HTTPError as e: # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404: # 404: username not found
            return jsonify({"error": "Invalid credentials."}), 401
        elif e.response.status_code == 400: # programming error, we mask as invalid credentials to users
            return jsonify({"error": "Invalid credentials."}), 401
        else: # other errors
            return jsonify({"error": "Service temporarily unavailable."}), 503
    except requests.RequestException as e: # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable."}), 503
 

def logout():   
    # check if user is logged in
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    # remove session cookie to log out
    session.clear()

    # send response to user
    return jsonify({"message": "Logout successful."}), 200


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
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = { "uuid": uuid_to_register, "username": username_to_register, "email": email_to_register, "password": password_hashed }
            url = "http://db_manager:8080/db_manager/auth/register"
            response = requests.post(url, json=payload)
            response.raise_for_status() # if response is obtained correctly 
            return response.json()
        
        response_data = make_request_to_dbmanager()

        # visto che vogliamo che l'utente si auto-logghi quando si registra controlliamo che la registrazione abbia successo qui
        session['uuid'] = uuid_to_register
        session['uuid_hex'] = uuid_hex_to_register
        session['email'] = email_to_register
        session['username'] = username_to_register
        session['role'] = "USER"
        session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({"message": "Registration successful."}), 201
    except requests.HTTPError as e:
        if e.response.status_code == 409: # email already in use
            return jsonify({"error": "The provided username / email is already in use."}), 409
        else: # other errors
            return jsonify({"error": "Service temporarily unavailable."}), 503
    except requests.RequestException as e: # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503