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

from openapi_server.models.login200_response import Login200Response
from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest
from openapi_server import util

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL

from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError

from pybreaker import CircuitBreaker, CircuitBreakerError

# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def health_check():
    return jsonify({"message": "Service operational."}), 200

# received from auth_controller
def login():
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    login_request = connexion.request.get_json()
    username = login_request.get("username")

    mysql = current_app.extensions.get('mysql')

    connection = None
    cursor = None
    try:
        @circuit_breaker
        def make_request_to_db():
            # Query the database for user based on username in PROFILE and hash in USERS
            connection = mysql.connect()
            cursor = connection.cursor()
            query = """
                SELECT BIN_TO_UUID(u.uuid), u.uuid, u.email, p.username, u.role, u.password
                FROM users u
                JOIN profiles p ON u.uuid = p.uuid
                WHERE p.username = %s
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if result:
            user_uuid_str, user_uuid_hex, user_email, user_name, user_role, user_password = result
            payload = {
                "uuid": user_uuid_str,
                "uuid_hex": str(user_uuid_hex),
                "email": user_email,
                "username": user_name,
                "role": user_role,
                "password": user_password
            }
            return jsonify(payload), 200
        else:
            return jsonify({"error": "Invalid username."}), 404
    except OperationalError as e: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ username +"]: Operational error.")
        return "", 500
    except ProgrammingError as e: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ username +"]: Programming error.")
        return "", 400
    except InternalError as e: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ username +"]: Internal error.")
        return "", 500
    except InterfaceError as e: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ username +"]: Interface error.")
        return "", 500
    except DatabaseError as e: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ username +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


# received from auth_controller
def register(register_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    login_request = connexion.request.get_json()
    uuid = login_request.get("uuid")
    username = login_request.get("username")
    email = login_request.get("email")
    password_hash = login_request.get("password")

    mysql = current_app.extensions.get('mysql')
    connection = None
    cursor = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            # Insert user in USERS table
            cursor.execute(
                'INSERT INTO users (uuid, email, password, role) VALUES (UUID_TO_BIN(%s), %s, %s, %s)',
                (uuid, email, password_hash, 'USER')
            )
            # Insert profile in PROFILE table
            cursor.execute(
                'INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES (UUID_TO_BIN(%s), %s, %s, %s)',
                (uuid, username, 0, 0)
            )
            connection.commit()
            return

        make_request_to_db()
        return "", 201
    except OperationalError as e: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ uuid +", "+ username +"]: Operational error.")
        return "", 500
    except ProgrammingError as e: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ uuid +", "+ username +"]: Programming error.")
        return "", 400
    except IntegrityError as e: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ uuid +", "+ username +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError as e: # if data format is invalid or out of range or size
        logging.error("Query ["+ uuid +", "+ username +"]: Data error.")
        return "", 400
    except InternalError as e: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ uuid +", "+ username +"]: Internal error.")
        return "", 500
    except InterfaceError as e: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ uuid +", "+ username +"]: Interface error.")
        return "", 500
    except DatabaseError as e: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ uuid +", "+ username +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


# received from feedback_controller
def feedback_send(user_uuid):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    feedback_request = connexion.request.get_json()["string"]
    user_uuid = connexion.request.get_json()["user_uuid"]

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
                (user_uuid, feedback_request)
            )
            connection.commit()
        
        make_request_to_db()
        return jsonify({"message": "Feedback created successfully"}), 200
        
    except OperationalError as e: # if connect to db fails means there is an error in the db
        return "", 500
    except ProgrammingError as e: # for example when you have a syntax error in your SQL or a table was not found
        return "", 400
    except InternalError as e: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        return "", 500
    except InterfaceError as e: # errors originating from Connector/Python itself, not related to the MySQL server
        return "", 500
    except DatabaseError as e: # default for any MySQL error which does not fit the other exceptions
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return "", 503