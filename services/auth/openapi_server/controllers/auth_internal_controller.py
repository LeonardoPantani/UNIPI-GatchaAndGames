import connexion
import jwt
import redis
import requests
from flask import jsonify
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

from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.models.userinfo_request import UserinfoRequest
from openapi_server.models.introspect_request import IntrospectRequest


SERVICE_TYPE = "auth"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])
redis_client = redis.Redis(host='redis', port=6379, db=0)


"""
    The object must be { "access_token": "eyJhbGciOiJIUzI1NiIsInR5...", "audience_required": "public_services"/"private_services" }
    This decrypts your access token and checks with REDIS that it is the same one saved by the user with the uuid written inside the token.
"""
def introspect(introspect_request=None):
    if not connexion.request.is_json: # checks if the request is a correct json
        return "", 400

    introspect_request = IntrospectRequest.from_dict(connexion.request.get_json())
    if not introspect_request.access_token or not introspect_request.audience_required:
        return "", 400

    if introspect_request.audience_required != "public_services" and introspect_request.audience_required != "private_services":
        return "", 400

    try:
        decoded_token = jwt.decode(introspect_request.access_token, "prova", algorithms=["HS256"], audience=introspect_request.audience_required)
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"]
        }

        saved_token = redis_client.get(decoded_token["uuid"]).decode("utf-8")

        if saved_token is not None and saved_token != introspect_request.access_token:
            send_log(f"Saved token for '{decoded_token["username"]}' is not the same as the saved one in Redis.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Unauthorized."}), 401

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired."}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Unauthorized."}), 401


"""
    The object must be { "access_token": "eyJhbGciOiJIUzI1NiIsInR5..." }
    This function just decrypts your access_token, without any further checks.
"""
def userinfo(userinfo_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    userinfo_request = UserinfoRequest.from_dict(connexion.request.get_json())
    if not userinfo_request.access_token:
        return "", 400
    
    try:
        decoded_token = jwt.decode(userinfo_request.access_token, "prova", algorithms=["HS256"], audience="public_services")
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"]
        }

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


""" Deletes a user. """
def delete_user_by_uuid(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "DELETE FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid,))
            connection.commit()
            return cursor.rowcount
        
        affected_rows = make_request_to_db()

        if affected_rows == 0:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"message": "User deleted."}), 200
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


""" Updates a user's email. """
def edit_email(session=None, uuid=None, email=None):
    if not uuid or not email:
        return jsonify({"error": "Invalid request."}), 400

    # verifying if user exists
    try:
        @circuit_breaker
        def make_request_to_db_1():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "SELECT 1 FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid,))
            cursor.fetchone()
            connection.commit()
            return cursor.rowcount
        
        affected_rows = make_request_to_db_1()

        if affected_rows == 0:
            return jsonify({"error": "User not found."}), 404
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query 1: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    # updating email
    try:
        @circuit_breaker
        def make_request_to_db_2():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "UPDATE users SET email = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (email, uuid))
            connection.commit()
            return cursor.rowcount
        
        affected_rows = make_request_to_db_2()

        if affected_rows == 0:
            return jsonify({"error": "No changes applied."}), 304
        
        return jsonify({"message": "Email updated."}), 200
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query 2: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


""" Returns user hashed password. """
def get_hashed_password(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "SELECT password FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if not result:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"password": result["password"]}), 200
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


""" Returns role of the user. """
def get_role_by_uuid(session=None, uuid=None):
    
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "SELECT role FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid,))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if not result:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"role": result["role"].upper()}), 200
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


""" Returns user info. """
def get_user(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = "SELECT BIN_TO_UUID(uuid) as uuid, email, role FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if not result:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"uuid": result["uuid"], "email": result["email"], "role": result["role"].upper()}), 200
    
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__}", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error: request_to_db", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503