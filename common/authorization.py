import requests
from functools import wraps
from flask import jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)

def verify_login(auth_header=None, audience_required="public_services"):
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing Authorization header"}), 401
    
    access_token = auth_header.split(" ")[1]
    if not access_token: # checks if after "Bearer " there is text
        return "", 400
    
    if audience_required != "public_services" and audience_required != "private_services":
        return "", 400

    try:
        @circuit_breaker
        def make_request_to_auth():
            payload = { "access_token": access_token, "audience_required": audience_required }
            url = "https://service_auth/auth/internal/introspect/"
            response = requests.post(url, json=payload, verify=False)
            response.raise_for_status()
            return response.json()

        session = make_request_to_auth()

        return session, 200
    except requests.HTTPError as e:
        if e.response.status_code == 401: # unauthorized
            return jsonify({"error": "This account is not authorized to perform this action."}), e.response.status_code
        elif e.response.status_code == 402: # token expired
            return jsonify({"error": "Login token expired. Please log-in again."}), e.response.status_code
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503