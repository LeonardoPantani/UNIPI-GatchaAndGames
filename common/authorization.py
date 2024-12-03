import inspect

import requests
from flask import current_app, jsonify
from openapi_server.helpers.logging import send_log
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=5,
    exclude=[requests.HTTPError],
)


def verify_login(auth_header=None, audience_required="public_services", service_type="unknown"):
    log_endpoint = inspect.stack()[1][3] # obtains function that called me to insert into logs
    
    if not auth_header or not auth_header.startswith("Bearer "):
        send_log("VerifyLogin: Not logged in.", service_type=service_type, level="general", endpoint=log_endpoint)
        return jsonify({"error": "Not logged in."}), 401

    access_token = auth_header.split(" ")[1]
    if not access_token:  # checks if after "Bearer " there is text
        send_log("VerifyLogin: Empty Bearer token.", service_type=service_type, level="general", endpoint=log_endpoint)
        return "", 400

    if audience_required != "public_services" and audience_required != "private_services":
        return "", 400

    try:

        @circuit_breaker
        def make_request_to_auth():
            payload = {"access_token": access_token, "audience_required": audience_required}
            url = "https://service_auth/auth/internal/introspect/"
            response = requests.post(url, json=payload, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        session = make_request_to_auth()

        return session, 200
    except requests.HTTPError as e:
        if e.response.status_code == 401:  # unauthorized
            send_log(
                "VerifyLogin: Account unauthorized.", level="info", service_type=service_type, endpoint=log_endpoint
            )
            return jsonify({"error": "This account is not authorized to perform this action."}), e.response.status_code
        elif e.response.status_code == 402:  # token expired
            send_log("VerifyLogin: Token expired.", level="info", service_type=service_type, endpoint=log_endpoint)
            return jsonify({"error": "Login token expired. Please log-in again."}), e.response.status_code
        else:
            send_log("VerifyLogin: HTTP Error.", level="error", service_type=service_type, endpoint=log_endpoint)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log(
            "VerifyLogin: RequestException Error.", service_type=service_type, level="error", endpoint=log_endpoint
        )
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("VerifyLogin: CircuitBreaker Error.", service_type=service_type, level="info", endpoint=log_endpoint)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503