import datetime
import re
import uuid

import bcrypt
import connexion
import jwt
import redis
import requests
from flask import current_app, jsonify, request
from mysql.connector.errors import (
    DatabaseError,
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest

SERVICE_TYPE = "auth"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])
redis_client = redis.Redis(host='redis', port=6379, db=0)


""" Returns 200 if service is healthy. """
def auth_health_check_get():
    return jsonify({"message": "Service operational."}), 200


""" Logs a user into the game. Accepts username and password. This acts as token endpoint. """
def login(login_request=None):
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    login_request = LoginRequest.from_dict(connexion.request.get_json())
    username_to_login = login_request.username
    password_to_login = login_request.password

    # /profile/internal/get_uuid_from_username
    # obtaining UUID from username
    try:
        @circuit_breaker
        def request_to_profile_service():
            params = { "username": username_to_login }
            url = "https://service_profile/profile/internal/get_uuid_from_username"
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        
        uuid = request_to_profile_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404: # user not found, hiding as 401
            return jsonify({"error": "Invalid credentials."}), 401
        else:
            send_log("HTTP Error", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log("Request Exception", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_profile_service", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    
    # query to database
    try:
        @circuit_breaker
        def request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            query = """
                SELECT BIN_TO_UUID(uuid) as uuid, uuid as uuid_hex, email, role, password
                FROM users
                WHERE uuid = UUID_TO_BIN(%s)
            """
            cursor.execute(query, (uuid,))
            return cursor.fetchone()
        
        result = request_to_db()
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    # invalid credentials
    if not result:
        return jsonify({"error": "Invalid credentials."}), 401
    
    user_uuid_str, user_uuid_hex, user_email, user_role, user_password = result
    result = {
        "uuid": user_uuid_str,
        "uuid_hex": str(user_uuid_hex),
        "email": user_email,
        "username": username_to_login,
        "role": user_role,
        "password": user_password
    }

    # password check
    if not bcrypt.checkpw(password_to_login.encode("utf-8"), result["password"].encode("utf-8")):
        send_log(f"User '{username_to_login}' used invalid credentials.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Invalid credentials."}), 401

    # REDIS
    try:
        if redis_client.exists(result["uuid"]):
            redis_client.delete(result["uuid"]) # if the user is already logged in, we disconnect him and give him an error, but then he can log in again correctly
            return jsonify({"message": "Already logged in."}), 409
    except redis.RedisError as e:
        send_log(f"Login: Redis error {e}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    try:
        token = complete_access(result["uuid"], result["uuid_hex"], result["email"], result["username"], result["role"])
    except redis.RedisError as e:
        send_log(f"Login: Redis error {e}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    send_log(f"User '{result["username"]}' logged in.", level="general", service_type=SERVICE_TYPE)
    response = jsonify({"message": "Login successful."})
    response.headers["Authorization"] = token
    return response, 200


""" Allows an account to log out. """
def logout():
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione
    
    user_id = session["uuid"]
    username = session["username"]

    # REDIS
    try:
        if not redis_client.exists(user_id):
            return jsonify({"error": "Not logged in."}), 403

        if redis_client.delete(user_id) == 0:
            return jsonify({"error": "Not logged in."}), 403
    except redis.RedisError as e:
        send_log(f"Logout: Redis error {e}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    # logout OK
    send_log(f"User '{username}' logged out.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message": "Logout successful."}), 200


""" Registers a new user account with username, email, and password. """
def register(register_request=None):
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    # authentication check
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] == 200: # is logged
        return jsonify({"message": "You are already logged in."}), 401

    # defines role for registration based on source gateway header
    source_gateway = request.headers.get('X-Source-Gateway', 'Unknown')
    role = ("ADMIN" if source_gateway == "Gateway-Private" else "USER")

    # obtaining dict of request
    register_request = RegisterRequest.from_dict(connexion.request.get_json())

    # verifying mail
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', register_request.email):
        send_log("Invalid email provided.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "The specified email is not valid."}), 406

    # hashing
    password_hashed = bcrypt.hashpw(register_request.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # generating UUID
    uuid_hex_to_register = uuid.uuid4().bytes
    uuid_to_register = str(uuid.UUID(bytes=uuid_hex_to_register))

    # query to database
    connection = get_db()
    try:
        @circuit_breaker
        def request_to_db():
            cursor = connection.cursor()
            connection.start_transaction()
            cursor.execute(
                'INSERT INTO users (uuid, email, password, role) VALUES (UUID_TO_BIN(%s), %s, %s, %s)',
                (uuid_to_register, register_request.email, password_hashed, role)
            )
            return

        request_to_db()
    except IntegrityError: # email already in use
        send_log(f"For username '{register_request.username}', email chosen '{register_request.email}' already exists.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "The provided username / email is already in use."}), 503
    except (OperationalError, DataError, ProgrammingError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    # /profile/internal/insert_profile
    # creates a profile.
    try:
        @circuit_breaker
        def request_to_profile_service():
            params = { "user_uuid": uuid_to_register, "username": register_request.username }
            url = "https://service_profile/profile/internal/insert_profile"
            response = requests.post(url, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        
        request_to_profile_service()
    except requests.HTTPError as e:
        connection.rollback()
        if e.response.status_code == 409: # username already exists
            send_log(f"For email '{register_request.email}', username chosen '{register_request.username}' already exists.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "The provided username / email is already in use."}), 409
        else:
            send_log("HTTP Error", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        connection.rollback()
        send_log("Request Exception", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        connection.rollback()
        send_log("CircuitBreaker Error: request_to_profile_service", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    connection.commit()

    # auto login
    try:
        token = complete_access(uuid_to_register, uuid_hex_to_register, register_request.email, register_request.username, role)
    except redis.RedisError as e:
        send_log(f"Login: Redis error {e}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    send_log("Registration of user '"+ register_request.username +"' completed.", level="general", service_type=SERVICE_TYPE)
    response = jsonify({"message": "Registration successful."})
    response.headers["Authorization"] = token
    return response, 201




""" Receives: uuid, uuid_hex, email, username, role 
    Throws: redis.RedisError """
def complete_access(uuid, uuid_hex, email, username, role):
    aud = ["public_services"]
    if role == "ADMIN":
        aud.append("private_services")

    # creating JWT token
    access_token_payload = {
        "iss": "https://" + SERVICE_TYPE,
        "sub": uuid,
        "email": email,
        "username": username,
        "uuid": uuid,
        "uuidhex": str(uuid_hex),
        "role": role,
        "logindate": datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
        "aud": aud,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=24 * 60 * 60)) # 1 day
    }
    access_token = jwt.encode(access_token_payload, current_app.config['jwt_secret_key'], algorithm="HS256")

    # adding token to REDIS
    redis_client.set(uuid, access_token, ex=24 * 60 * 60) # 1 day
    
    # returning token
    return f'Bearer {access_token}'