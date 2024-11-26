import uuid
import re
from datetime import datetime
import bcrypt
import connexion
import requests
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest
from openapi_server.models.register_request import RegisterRequest
from openapi_server import util
from openapi_server.helpers.logging import send_log, query_logs
from flask import jsonify, session, request
from pybreaker import CircuitBreaker, CircuitBreakerError

SERVICE_TYPE = "auth"


circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=5, exclude=[requests.HTTPError])




def auth_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def login():
    if "username" in session:
        return jsonify({"error": "You are already logged in."}), 409

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid json request
    login_request = LoginRequest.from_dict(connexion.request.get_json())
    username_to_login = login_request.username
    password_to_login = login_request.password

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {"username": username_to_login}
            url = "http://db_manager:8080/db_manager/auth/login"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response_data = make_request_to_dbmanager()

        if bcrypt.checkpw(password_to_login.encode("utf-8"), response_data["password"].encode("utf-8")):  # wrong password
            session["uuid"] = response_data["uuid"]
            session["uuid_hex"] = response_data["uuid_hex"]
            session["email"] = response_data["email"]
            session["username"] = response_data["username"]
            session["role"] = response_data["role"]
            session["login_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            send_log("User '" + username_to_login + "' logged in.", level="general", service_type=SERVICE_TYPE)
            return jsonify({"message": "Login successful."}), 200
            
        else:
            send_log("User '" + username_to_login + "' used invalid credentials.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Invalid credentials."}), 401

    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:  # username not found
            return jsonify({"error": "Invalid credentials."}), 401
        elif e.response.status_code == 400:  # programming error, we mask as invalid credentials to users
            return jsonify({"error": "Invalid credentials."}), 401
        else:  # other errors
            send_log("Service unavailable.", level="warning", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        send_log("RequestException.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log("CircuitBreakerError.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def logout():
    # check if user is logged in
    if "username" not in session:
        return jsonify({"error": "Not logged in."}), 403

    # adding to log
    send_log("User '" + session['username'] + "' logged out.", level="general", service_type=SERVICE_TYPE)


    # remove session cookie to log out
    session.clear()

    # send response to user
    return jsonify({"message": "Logout successful."}), 200


def register():
    if "username" in session:
        return jsonify({"error": "You are already logged in."}), 401

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    source_gateway = request.headers.get('X-Source-Gateway', 'Unknown')
    if source_gateway == "Gateway-Private":
        role = "ADMIN"
    else:
        role = "USER"

    # valid json request
    register_request = RegisterRequest.from_dict(connexion.request.get_json())
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', register_request.email):
        send_log("Invalid email provided.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "The specified email is not valid."}), 406
    username_to_register = register_request.username
    email_to_register = register_request.email
    password_to_hash = register_request.password

    # hashing
    password_hashed = bcrypt.hashpw(password_to_hash.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # generating UUID
    uuid_hex_to_register = uuid.uuid4().bytes
    uuid_to_register = str(uuid.UUID(bytes=uuid_hex_to_register))

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "uuid": uuid_to_register,
                "username": username_to_register,
                "email": email_to_register,
                "password": password_hashed,
                "role": role
            }
            url = "http://db_manager:8080/db_manager/auth/register"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_dbmanager()

        #  since we want the user to self-login when registering we check for successful registration here

        session["uuid"] = uuid_to_register
        session["uuid_hex"] = uuid_hex_to_register
        session["email"] = email_to_register
        session["username"] = username_to_register
        session["role"] = "USER"
        session["login_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        send_log("Registration of user '"+ username_to_register +"' completed.", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": "Registration successful."}), 201
    except requests.HTTPError as e:
        if e.response.status_code == 409:  # username / email already in use
            return jsonify({"error": "The provided username / email is already in use."}), 409
        else:  # other errors
            send_log("Service unavailable.", level="warning", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        send_log("RequestException.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log("CircuitBreakerError.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503