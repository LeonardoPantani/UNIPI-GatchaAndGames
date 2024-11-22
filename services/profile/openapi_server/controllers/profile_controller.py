import traceback
import connexion
import bcrypt
import pymysql
import logging
import requests

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.delete_profile_request import DeleteProfileRequest  # noqa: E501
from openapi_server.models.edit_profile_request import EditProfileRequest  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import session, current_app, jsonify

from pybreaker import CircuitBreaker, CircuitBreakerError


def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


def delete_profile():  # noqa: E501
    try:
        # Get database connection with circuit breaker protection
        mysql = current_app.extensions.get('mysql')

        conn = mysql.connect()
        cursor = conn.cursor()

        user_uuid = session.get('uuid')

        if not user_uuid:
            return jsonify({"error": "Not logged in"}), 403

        if connexion.request.is_json:
            try:
                delete_profile_request = DeleteProfileRequest.from_dict(connexion.request.get_json())
            except Exception as e:
                return jsonify({"error": "Invalid request format"}), 400

            try: # /db_manager/profile/get_user_info
                cursor.execute('SELECT BIN_TO_UUID(uuid), password FROM users WHERE uuid = UUID_TO_BIN(%s)', (user_uuid,))
                result = cursor.fetchone()
            except Exception as e:
                return jsonify({"error": "Database error"}), 500

            if not result:
                return jsonify({"error": "User not found"}), 404
            
            if not bcrypt.checkpw(delete_profile_request.password.encode('utf-8'), result[1].encode('utf-8')):
                return jsonify({"error": "Invalid password"}), 400


            user_uuid = result[0]

            # Delete from tables in correct order due to foreign keys
            # /db_manager/profile/delete
            cursor.execute('DELETE FROM feedbacks WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))
            cursor.execute('DELETE FROM ingame_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,)) 
            cursor.execute('DELETE FROM bundles_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))

            cursor.execute('''
                           UPDATE profiles SET currency = currency + (
                                SELECT current_bid
                                FROM auctions
                                WHERE item_uuid IN (
                                    SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                                )
                            )
                           WHERE uuid IN (
                                SELECT current_bidder
                                FROM auctions
                                WHERE item_uuid IN (
                                    SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                                )
                           )
                           ''',
                           (user_uuid, user_uuid)
            )
            
            cursor.execute('DELETE FROM pvp_matches WHERE player_1_uuid = UUID_TO_BIN(%s) OR player_2_uuid = UUID_TO_BIN(%s)', (user_uuid,user_uuid))
            cursor.execute('UPDATE auctions SET current_bid = 0, current_bidder = NULL WHERE current_bidder = UUID_TO_BIN(%s)', (user_uuid))
            cursor.execute('DELETE FROM auctions WHERE item_uuid IN (SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s))', (user_uuid,))
            cursor.execute('DELETE FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)', (user_uuid,))

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
        mysql = current_app.extensions.get('mysql')

        conn = mysql.connect()
        cursor = conn.cursor()

        # Get username from session
        username = session.get('username')
        
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
            # /db_manager/profile/get_user_hashed_psw
            response = requests.post(
            'http://db_manager:8080/db_manager/profile/get_user_hashed_psw',
            json={"user_uuid": session.get('uuid')}
            )
            
            if response.status_code == 404:
                return jsonify({"error": "User not found"}), 404

            hashed_password = response.json().get('password') 
            
                    # Verify password
            if not edit_request.password or not bcrypt.checkpw(
            edit_request.password.encode('utf-8'),
            hashed_password.encode('utf-8')
            ):
                return jsonify({"error": "Invalid password"}), 403

            # If password verified, proceed with updates
            updates = []
            params = []
            
            if edit_request.email:
                updates.append("u.email = %s")
                params.append(edit_request.email)
                
            if edit_request.username:
                updates.append("p.username = %s")
                params.append(edit_request.username)

            if updates:  # /db_manager/profile/edit
                try:
                    response = requests.post(
                        'http://db_manager:8080/db_manager/profile/edit',
                        json={
                            "user_uuid": session.get('uuid'),
                            "email": edit_request.email,
                            "username": edit_request.username
                        }
                    )
                    
                    if response.status_code == 404:
                        return jsonify({"error": "User not found"}), 404
                    elif response.status_code == 304:
                        return jsonify({"message": "No changes needed"}), 304
                    elif response.status_code != 200:
                        return jsonify({"error": "Error updating profile"}), 500
                    
                    # Update session if username changed
                    if edit_request.username:
                        session['username'] = edit_request.username

                    return jsonify({"message": "Profile updated successfully"}), 200

                except requests.RequestException:
                    return jsonify({"error": "Service temporarily unavailable"}), 503
                        

   

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
            mysql = current_app.extensions.get('mysql')

            conn = mysql.connect()
        except CircuitBreakerError as cbe:
            logging.error(f"Circuit Breaker Open: {str(cbe)}")
            return jsonify({"error": "Service unavailable. Please try again later."}), 503
        except ConnectionError as ce:
            logging.error(f"Database connection error: {str(ce)}")
            return jsonify({"error": "Database connection not initialized"}), 500
            
        cursor = conn.cursor()
        
        # Get user info from database
        # /db_manager/profile/get_user_info
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
