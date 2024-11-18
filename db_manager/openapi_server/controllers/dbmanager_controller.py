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
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)


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


def register(register_request=None):
    if not connexion.request.is_json:
        return jsonify({"error": "Bad request."}), 400
    
    login_request = connexion.request.get_json()
    uuid = login_request.get("uuid")
    username = login_request.get("username")
    email = login_request.get("email")
    password_hash = login_request.get("password")

    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        # Begin transaction
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

        # Commit transaction
        connection.commit()

        return jsonify({"message": "Successful registration."}), 201
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except mysql.connect().IntegrityError:
        # Duplicate email error
        connection.rollback()
        return jsonify({"error": "The provided email or username are already in use."}), 409
    except Exception as e:
        # Rollback transaction on error
        logging.error(f"Unexpected error during registration: {str(e)}")
        connection.rollback()
        return jsonify({"error": str(e)}), 500