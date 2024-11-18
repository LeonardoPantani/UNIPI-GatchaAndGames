import traceback
import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.delete_profile_request import DeleteProfileRequest  # noqa: E501
from openapi_server.models.edit_profile_request import EditProfileRequest  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util
from flask import session, current_app, jsonify
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError
import bcrypt
import pymysql


def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200



def get_database_connection():
    """
    Function to get a database connection 
    """
    mysql = current_app.extensions.get('mysql')
    if not mysql:
        raise CircuitBreakerError("Database connection not initialized")
    conn = mysql.connect() 
    if not conn:
        raise CircuitBreakerError("Failed to establish database connection")
    return conn


def delete_profile():  # noqa: E501
    """Deletes this account."""
    conn = None
    cursor = None
    try:
        # Get database connection with circuit breaker protection
        conn = get_database_connection()
        cursor = conn.cursor()

        # Get username from flask session
        username = session.get('username')
        logging.info(f"Username from session: {username}")

        if not username:
            return jsonify({"error": "Not logged in"}), 403

        if connexion.request.is_json:
            try:
                delete_profile_request = DeleteProfileRequest.from_dict(connexion.request.get_json())
                logging.info(f"Request data: {delete_profile_request}")
            except Exception as e:
                logging.error(f"Error parsing request: {str(e)}")
                return jsonify({"error": "Invalid request format"}), 400

            try:
                cursor.execute('SELECT BIN_TO_UUID(u.uuid) as uuid, u.password FROM users u JOIN profiles p ON u.uuid = p.uuid WHERE p.username = %s', (username,))
                result = cursor.fetchone()
                logging.info(f"DB result: {result}")
            except Exception as e:
                logging.error(f"Database error: {str(e)}")
                return jsonify({"error": "Database error"}), 500

            if not result:
                return jsonify({"error": "User not found"}), 404
            
            if not bcrypt.checkpw(delete_profile_request.password.encode('utf-8'), result[1].encode('utf-8')):
                return jsonify({"error": "Invalid password"}), 400


            user_uuid = result[0]

            # Delete from tables in correct order due to foreign keys
            cursor.execute('DELETE FROM feedbacks WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))
            cursor.execute('DELETE FROM ingame_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,)) 
            cursor.execute('DELETE FROM bundles_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))
            cursor.execute('DELETE FROM profiles WHERE uuid = UUID_TO_BIN(%s)', (user_uuid,))
            cursor.execute('DELETE FROM users WHERE uuid = UUID_TO_BIN(%s)', (user_uuid,))

            conn.commit()
            
            # Clear session
            session.clear()
            
            return jsonify({"message": "Profile deleted successfully"}), 200

        return jsonify({"error": "Invalid request"}), 400
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def edit_profile():  # noqa: E501
    """Edits properties of the profile."""
    conn = None 
    cursor = None
    try:
        # Get database connection with circuit breaker protection
        conn = get_database_connection()
        cursor = conn.cursor()

        # Get username from session
        username = session.get('username')
        logging.info(f"Username from session: {username}")
        
        if not username:
            return jsonify({"error": "Not logged in"}), 403

        if connexion.request.is_json:
            try:
                edit_request = EditProfileRequest.from_dict(connexion.request.get_json())
                logging.info(f"Request data: {edit_request}")
            except Exception as e:
                logging.error(f"Error parsing request: {str(e)}")
                return jsonify({"error": "Invalid request format"}), 400

            # First verify the password like in delete_profile
            cursor.execute(
                'SELECT BIN_TO_UUID(u.uuid) as uuid, u.password FROM users u JOIN profiles p ON u.uuid = p.uuid WHERE p.username = %s', 
                (username,)
            )
            result = cursor.fetchone()

            if not result:
                return jsonify({"error": "User not found"}), 404
            
            # Verify password using bcrypt
            if not edit_request.password or not bcrypt.checkpw(
                edit_request.password.encode('utf-8'), 
                result[1].encode('utf-8')
            ):
                return jsonify({"error": "Invalid password"}), 400

            # If password verified, proceed with updates
            updates = []
            params = []
            
            if edit_request.email:
                updates.append("u.email = %s")
                params.append(edit_request.email)
                
            if edit_request.username:
                updates.append("p.username = %s")
                params.append(edit_request.username)

            if updates:
                params.append(username)  # Add current username for WHERE clause
                query = f"""
                    UPDATE users u JOIN profiles p ON u.uuid = p.uuid 
                    SET {', '.join(updates)}
                    WHERE p.username = %s
                """
                cursor.execute(query, params)
                conn.commit()

                # Update session if username changed
                if edit_request.username:
                    session['username'] = edit_request.username

                return jsonify({"message": "Profile updated successfully"}), 200
            
            return jsonify({"error": "No fields to update"}), 400

   

    except Exception as e:
        
        return jsonify({"error": "Error occurred"}), 500
    

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_info(uuid):  # noqa: E501
    """Returns infos about a UUID."""
    conn = None
    cursor = None
    try:
        # Get database connection with circuit breaker protection
        try:
            conn = get_database_connection()
        except CircuitBreakerError as cbe:
            logging.error(f"Circuit Breaker Open: {str(cbe)}")
            return jsonify({"error": "Service unavailable. Please try again later."}), 503
        except ConnectionError as ce:
            logging.error(f"Database connection error: {str(ce)}")
            return jsonify({"error": "Database connection not initialized"}), 500
            
        cursor = conn.cursor()
        
        # Get user info from database
        cursor.execute('''
            SELECT BIN_TO_UUID(u.uuid) as id, p.username, u.email, p.created_at 
            FROM users u 
            JOIN profiles p ON u.uuid = p.uuid 
            WHERE u.uuid = UUID_TO_BIN(%s)
        ''', (uuid,))
        
        result = cursor.fetchone()
        logging.info(f"DB result: {result}")
        
        if not result:
            return jsonify({"error": "User not found"}), 404

        # Create User object with results
        user = User(
            id=result[0],
            username=result[1],
            email=result[2], 
            joindate=result[3]
        )

        return jsonify(user.to_dict()), 200

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

    

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
