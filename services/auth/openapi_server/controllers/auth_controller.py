import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL


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
                SELECT u.password, u.uuid 
                FROM users u
                JOIN profiles p ON u.uuid = p.uuid
                WHERE p.username = %s
            """
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            cursor.close()

            if result:
                #stored_password_hash, user_uuid = result
                #if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                    # Create session cookie on successful login
                response = make_response(jsonify({"message": "Login successful"}), 200)
                session['username'] = username
                return response
            else:
                return jsonify({"error": "Invalid credentials"}), 401
            #else:
            #    return jsonify({"error": "Invalid credentials"}), 401

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Invalid request"}), 400


def logout():   
    # Check if user is logged in
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    # Remove session cookie to log out
    response = make_response(jsonify({"message": "Logout successful"}), 200)
    session.clear()
    return response


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
        user_uuid = uuid.uuid4().bytes

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
                (user_uuid, email, password_hash, 'USER')
            )
            
            # Insert profile in PROFILE table
            cursor.execute(
                'INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES (%s, %s, %s, %s)',
                (user_uuid, username, 0, 0)
            )

            # Commit transaction
            connection.commit()

            cursor.close()
            connection.close()

            # adding username to session
            session['username'] = username

            return jsonify({"message": "Registration successful"}), 201

        except mysql.connect().IntegrityError:
            # Duplicate email error
            connection.rollback()
            return jsonify({"error": "The provided email address is already in use"}), 409
        except Exception as e:
            # Rollback transaction on error
            connection.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Invalid request"}), 400
