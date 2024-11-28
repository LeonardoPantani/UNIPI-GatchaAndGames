import uuid
import re
import datetime
import bcrypt
import connexion
import requests
import jwt
import redis
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest
from openapi_server import util
from openapi_server.helpers.logging import send_log, query_logs
from flask import jsonify, session, request
from pybreaker import CircuitBreaker, CircuitBreakerError

SERVICE_TYPE = "auth"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])
redis_client = redis.Redis(host='redis', port=6379, db=0)


def auth_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def login(login_request=None):
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid json request
    login_request = LoginRequest.from_dict(connexion.request.get_json())
    username_to_login = login_request.username
    password_to_login = login_request.password

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {"username": username_to_login}
            url = "http://db_manager:8080/db_manager/auth/login"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response_data = make_request_to_dbmanager()

        # Verifica se l'utente è già loggato (a questo punto le credenziali sono già ok)
        user_id = response_data["uuid"]
        if redis_client.exists(user_id):
            redis_client.delete(user_id) # se l'utente è già loggato lo scolleghiamo e gli diamo errore, ma così potrà rifare il login a modo
            return jsonify({"message": "Previous session invalidated successfully. Login again."}), 409

        # Verifica la password
        if bcrypt.checkpw(password_to_login.encode("utf-8"), response_data["password"].encode("utf-8")):
            # Crea i payload JWT
            access_token_payload = {
                "iss": "http://service_auth:8080",
                "sub": user_id,
                "email": response_data["email"],
                "username": response_data["username"],
                "uuid": response_data["uuid"],
                "uuidhex": response_data["uuid_hex"],
                "role": response_data["role"],
                "logindate": datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                "aud": "public_services",
                "iat": datetime.datetime.now(datetime.timezone.utc),
                "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)), # 3600 secondi
                "scope": "access",
            }

            
            # Genera il token
            access_token = jwt.encode(access_token_payload, "prova", algorithm="HS256")

            # Aggiungi il token a redis
            redis_client.set(user_id, access_token, ex=3600)

            # Logga l'azione
            send_log(f"User '{username_to_login}' logged in.", level="general", service_type=SERVICE_TYPE)

            # Invia i token negli header
            response = jsonify({"message": "Login successful."})
            response.headers["Authorization"] = f'Bearer {access_token}'
            return response, 200
        else:
            send_log(f"User '{username_to_login}' used invalid credentials.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Invalid credentials."}), 401

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Invalid credentials."}), 401
        return jsonify({"error": "Service temporarily unavailable. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503



def logout():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 403

    token = auth_header.split(" ")[1]

    try:
        # Decodifica il token per ottenere l'user_id
        decoded_token = jwt.decode(token, "prova", algorithms=["HS256"], audience="public_services")
        user_id = decoded_token["sub"]

        # Controlla se la chiave esiste in Redis
        if not redis_client.exists(user_id):
            return jsonify({"error": "Invalid request. User is not logged in."}), 400

        # Rimuovi l'associazione da Redis e verifica se è stata rimossa
        deleted = redis_client.delete(user_id)
        if deleted == 0:
            return jsonify({"error": "Invalid request. User is not logged in."}), 400

        send_log(f"User '{decoded_token['sub']}' logged out.", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": "Logout successful."}), 200

    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token."}), 403



def register(register_request):
    if "username" in session:
        return jsonify({"error": "You are already logged in."}), 401

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    source_gateway = request.headers.get('X-Source-Gateway', 'Unknown')
    if source_gateway == "Gateway-Private":
        role = "ADMIN"
    else:
        role = "USER"

    # valid json request
    register_request = RegisterRequest.from_dict(connexion.request.get_json())
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', register_request.email):
        send_log("Invalid email provided.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "The specified email is not valid."}), 406
    username_to_register = register_request.username
    email_to_register = register_request.email
    password_to_hash = register_request.password

    # hashing
    password_hashed = bcrypt.hashpw(password_to_hash.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # generating UUID
    uuid_hex_to_register = uuid.uuid4().bytes
    uuid_to_register = str(uuid.UUID(bytes=uuid_hex_to_register))

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "uuid": uuid_to_register,
                "username": username_to_register,
                "email": email_to_register,
                "password": password_hashed,
                "role": role
            }
            url = "http://db_manager:8080/db_manager/auth/register"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_dbmanager()

        #  since we want the user to self-login when registering we check for successful registration here

        session["uuid"] = uuid_to_register
        session["uuid_hex"] = uuid_hex_to_register
        session["email"] = email_to_register
        session["username"] = username_to_register
        session["role"] = "USER"
        session["login_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        send_log("Registration of user '"+ username_to_register +"' completed.", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": "Registration successful."}), 201
    except requests.HTTPError as e:
        if e.response.status_code == 409:  # username / email already in use
            return jsonify({"error": "The provided username / email is already in use."}), 409
        else:  # other errors
            send_log("Service unavailable.", level="warning", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        send_log("RequestException.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log("CircuitBreakerError.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
