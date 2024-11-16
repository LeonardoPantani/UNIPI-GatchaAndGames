import connexion
import uuid
import bcrypt
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
    
    if connexion.request.is_json:
        login_request = connexion.request.get_json()
        username = login_request.get("username")
        password = login_request.get("password")

        # Check for missing fields
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400

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
                if bcrypt.checkpw(password.encode('utf-8'), user_password.encode('utf-8')):
                    # Create session cookie on successful login
                    response = make_response(jsonify({"message": "Login successful"}), 200)
                    session['uuid'] = user_uuid_str
                    session['uuid_hex'] = user_uuid_hex
                    session['email'] = user_email
                    session['username'] = user_name
                    session['role'] = user_role
                    session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return response
                else:
                    return jsonify({"error": "Invalid credentials"}), 401
            else: 
                return jsonify({"error": "Invalid credentials"}), 401

        except CircuitBreakerError:
            logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
            return jsonify({"error": "Service unavailable. Please try again later."}), 503

        except Exception as e:
            logging.error(f"Unexpected error during login: {str(e)}")
            return jsonify({"error": str(e)}), 500

        finally:
            # Close the cursor and connection if they exist
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return jsonify({"message": "Invalid request"}), 400

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
    if connexion.request.is_json:
        register_request = connexion.request.get_json()
        username = register_request.get("username")
        email = register_request.get("email")
        password = register_request.get("password")

        # Check for missing fields
        if not username or not email or not password:
            return jsonify({"error": "Missing required fields"}), 400

        # Hash the password using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Generate UUID for new user
        user_uuid_hex = uuid.uuid4().bytes
        user_uuid_str = str(uuid.UUID(bytes=user_uuid_hex))

        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500

            # Begin transaction
            connection = mysql.connect()
            cursor = connection.cursor()

            # Insert user in USERS table
            cursor.execute(
                'INSERT INTO users (uuid, email, password, role) VALUES (%s, %s, %s, %s)',
                (user_uuid_hex, email, password_hash, 'USER')
            )
            
            # Insert profile in PROFILE table
            cursor.execute(
                'INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES (%s, %s, %s, %s)',
                (user_uuid_hex, username, 0, 0)
            )

            # Commit transaction
            connection.commit()

            # adding username to session
            session['uuid'] = user_uuid_str
            session['uuid_hex'] = user_uuid_hex
            session['email'] = email
            session['username'] = username
            session['role'] = "USER"
            session['login_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return jsonify({"message": "Registration successful"}), 201

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

    return jsonify({"message": "Invalid request"}), 400
