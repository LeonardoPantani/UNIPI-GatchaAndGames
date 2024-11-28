import requests
from flask import jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)

def verify_login(auth_header=None):
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    access_token = auth_header.split(" ")[1]

    try:
        @circuit_breaker
        def make_request_to_auth():
            payload = { "AccessToken": access_token }
            url = "http://service_auth:8080/auth/internal/introspect/"
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()

        session = make_request_to_auth()
    
        return session, 200
    except requests.HTTPError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503