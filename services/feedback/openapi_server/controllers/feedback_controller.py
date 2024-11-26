import connexion
import requests

from flask import jsonify, session
from openapi_server.helpers.logging import send_log
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)


def health_check():
    return jsonify({"message": "Service operational."}), 200


@circuit_breaker
def post_feedback():
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid json request
    feedback_request = connexion.request.get_json()["string"]
    if len(feedback_request) == 0:
        return jsonify({"message": "Invalid request."}), 400

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": session["uuid"],
                "string": feedback_request
            }
            url = "http://db_manager:8080/db_manager/feedback/submit"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_dbmanager()

        return jsonify({"message": "Feedback successfully submitted."}), 201
    except requests.HTTPError as e:
        if e.response.status_code == 400:  # programming error
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503