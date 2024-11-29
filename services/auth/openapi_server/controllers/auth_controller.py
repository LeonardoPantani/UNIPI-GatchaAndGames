import uuid
import re
import datetime
import bcrypt
import connexion
import requests
import jwt
import redis
import logging
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest
from openapi_server import util
from openapi_server.helpers.logging import send_log, query_logs
from flask import jsonify, session, request
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.db import get_db
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)

SERVICE_TYPE = "auth"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])
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
        def make_request_to_db():
            params = {"username": username_to_login}
            url = "http://service_profile:8080/profile/internal/get_uuid_from_username"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        uuid = make_request_to_db()

        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            query = """
                SELECT BIN_TO_UUID(uuid), uuid, email, role, password
                FROM users
                WHERE uuid = UUID_TO_BIN(%s)
            """
            cursor.execute(query, (uuid,))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if not result:
            return "", 404
        
        user_uuid_str, user_uuid_hex, user_email, user_role, user_password = result
        result = {
            "uuid": user_uuid_str,
            "uuid_hex": str(user_uuid_hex),
            "email": user_email,
            "username": username_to_login,
            "role": user_role,
            "password": user_password
        }

        # Verifica se l'utente è già loggato (a questo punto le credenziali sono già ok)
        user_id = result["uuid"]
        if redis_client.exists(user_id):
            redis_client.delete(user_id) # se l'utente è già loggato lo scolleghiamo e gli diamo errore, ma così potrà rifare il login a modo
            return jsonify({"message": "Previous session invalidated successfully. Login again."}), 409

        # Verifica la password
        if bcrypt.checkpw(password_to_login.encode("utf-8"), result["password"].encode("utf-8")):
            # Crea i payload JWT
            access_token_payload = {
                "iss": "http://service_auth:8080",
                "sub": user_id,
                "email": result["email"],
                "username": result["username"],
                "uuid": result["uuid"],
                "uuidhex": result["uuid_hex"],
                "role": result["role"],
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
    except OperationalError:
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query: Database error.")
        return "", 500


def logout():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not logged in."}), 403
    token = auth_header.split(" ")[1]

    # JWT
    try:
        decoded_token = jwt.decode(token, "prova", algorithms=["HS256"], audience="public_services")
    except jwt.InvalidTokenError:
        return jsonify({"error": "Not logged in."}), 403
    
    user_id = decoded_token["sub"]

    # REDIS
    try:
        if not redis_client.exists(user_id):
            return jsonify({"error": "Not logged in."}), 403

        if redis_client.delete(user_id) == 0:
            return jsonify({"error": "Not logged in."}), 403
    except redis.RedisError as e:
        send_log(f"Logout: Redis error {e}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    # Logout OK
    send_log(f"User '{decoded_token['sub']}' logged out.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message": "Logout successful."}), 200



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
            response.raise_for_status()
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
