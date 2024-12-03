############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import inspect
import connexion
import jwt
import redis
import requests
from flask import current_app, jsonify
from openapi_server.helpers.logging import send_log
from pybreaker import CircuitBreaker, CircuitBreakerError

MOCK_REDIS = {

}

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)

def verify_login(auth_header=None, audience_required="public_services", service_type="unknown"):
    log_endpoint = inspect.stack()[1][3]
    if not auth_header or not auth_header.startswith("Bearer "):
        send_log("VerifyLogin: Not logged in.", service_type=service_type, level="general", endpoint=log_endpoint)
        return jsonify({"error": "Not logged in."}), 401
    
    access_token = auth_header.split(" ")[1]
    if not access_token: # checks if after "Bearer " there is text
        send_log("VerifyLogin: Empty Bearer token.", service_type=service_type, level="general", endpoint=log_endpoint)
        return "", 400
    
    if audience_required != "public_services" and audience_required != "private_services":
        return "", 400
    
    try:
        @circuit_breaker
        def make_request_to_auth():
            # chiamata a introspect access_token e audience_required
            response = introspect(access_token, audience_required)
            return response

        response = make_request_to_auth()
        
        return response[0], response[1]
    except requests.HTTPError as e:
        if e.response.status_code == 401: # unauthorized
            send_log("VerifyLogin: Account unauthorized.", level="info", service_type=service_type, endpoint=log_endpoint)
            return jsonify({"error": "This account is not authorized to perform this action."}), e.response.status_code
        elif e.response.status_code == 402: # token expired
            send_log("VerifyLogin: Token expired.", level="info", service_type=service_type, endpoint=log_endpoint)
            return jsonify({"error": "Login token expired. Please log-in again."}), e.response.status_code
        else:
            send_log("VerifyLogin: HTTP Error.", level="error", service_type=service_type, endpoint=log_endpoint)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        send_log("VerifyLogin: RequestException Error.", service_type=service_type, level="error", endpoint=log_endpoint)
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log("VerifyLogin: CircuitBreaker Error.", service_type=service_type, level="info", endpoint=log_endpoint)
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def introspect(access_token, audience_required):
    if not access_token or not audience_required:
        return "", 400

    if audience_required != "public_services" and audience_required != "private_services":
        return "", 400

    try:
        decoded_token = jwt.decode(access_token, current_app.config['jwt_secret_key'], algorithms=["HS256"], audience=audience_required)
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"]
        }

        # obtaining token saved in Redis (mock)
        saved_token = access_token

        # if no token is saved probably is because Redis was restarted since user logged in
        if saved_token is None:
            send_log(f"Token for user {decoded_token["username"]} is valid but was not found in Redis.", level="warning", service_type="auth")
            return ({"error": "Unauthorized."}, 401)

        # if it is not equal to the one saved in Redis, it is a problem
        if saved_token != access_token:
            send_log(f"Saved token for '{decoded_token["username"]}' is not the same as the saved one in Redis.", level="info", service_type="auth")
            return ({"error": "Unauthorized."}, 401)

        return (result, 200)
    except jwt.ExpiredSignatureError:
        return ({"error": "Token expired."}, 402)
    except jwt.InvalidTokenError:
        return ({"error": "Unauthorized."}, 401)