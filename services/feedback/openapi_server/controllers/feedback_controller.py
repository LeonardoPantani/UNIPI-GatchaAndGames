
import connexion
import requests
from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server import util
from openapi_server.controllers.feedback_internal_controller import submit_feedback
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_string_input
from openapi_server.helpers.logging import send_log

SERVICE_TYPE = "admin"
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)


def feedback_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def post_feedback(string=None, session=None):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    # valid json request
    feedback_request = connexion.request.args.get("string")
    if len(feedback_request) == 0:
        return jsonify({"message": "Invalid request."}), 400

    feedback_request = sanitize_string_input(feedback_request)

    feedback = {"content": feedback_request}

    response = submit_feedback(feedback, None, session["uuid"])
    
    if response[1] != 201:
        send_log(f"submit_feedback: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    send_log(f"post_feedback: User {session['username']} has successfully submitted a feedback.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message": "Feedback successfully submitted."}), 201
