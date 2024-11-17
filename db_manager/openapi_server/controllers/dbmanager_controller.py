import connexion
import uuid
import bcrypt
import requests
import json
from datetime import datetime

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login200_response import Login200Response  # noqa: E501
from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def login():  # noqa: E501
    if not connexion.request.is_json:
        return jsonify({"error": "Bad request."}), 400
    
    login_request = connexion.request.get_json()
    username = login_request.get("username")

    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

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
        result = cursor.fetchone()

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
            return jsonify({"error": "Invalid username"}), 404
    except Exception as e:
            return jsonify({"error": str(e)}), 500
    finally:
        # Close the cursor and connection if they exist
        if cursor:
            cursor.close()
        if connection:
            connection.close()
    return jsonify({"error": "Service unavailable."}), 500


def register(register_request=None):  # noqa: E501
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
    finally:
        # Close the cursor and connection if they exist
        if cursor:
            cursor.close()
        if connection:
            connection.close()
