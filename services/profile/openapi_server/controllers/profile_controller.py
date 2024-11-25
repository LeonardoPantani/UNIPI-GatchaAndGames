import traceback
import connexion
import bcrypt
import logging
import requests

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.delete_profile_request import DeleteProfileRequest
from openapi_server.models.edit_profile_request import EditProfileRequest
from openapi_server.models.user import User
from openapi_server import util

from flask import session, jsonify

from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(
    fail_max=5, reset_timeout=5, exclude=[requests.HTTPError]
)

def health_check():
    return jsonify({"message": "Service operational."}), 200


def delete_profile():
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403
    
    delete_profile_request = DeleteProfileRequest.from_dict(connexion.request.get_json())
    password = delete_profile_request.password

    # /db_manager/profile/get_user_hashed_psw
    # Returns user's hashed password
    payload = {
        "user_uuid": session["uuid"]
    }
    
    user_password = ""
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/profile/get_user_hashed_psw"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        user_password = make_request_to_dbmanager()["password"]
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    if not bcrypt.checkpw(password.encode('utf-8'), user_password.encode('utf-8')):
        return jsonify({"error": "Invalid password."}), 400


    # /db_manager/profile/delete
    # Returns info about a specific user given his UUID
    payload = {
        "user_uuid": session["uuid"]
    }
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/profile/delete"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        make_request_to_dbmanager()

        session.clear()
        return jsonify({"message": "Profile deleted successfully"}), 200
    except requests.HTTPError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def edit_profile():
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not logged in."}), 403

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


def get_user_info(uuid):
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    # /db_manager/profile/get_user_info
    # Returns info about a specific user given his UUID
    payload = {
        "user_uuid": uuid
    }
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/profile/get_user_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        user = make_request_to_dbmanager()

        return user, 200
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503