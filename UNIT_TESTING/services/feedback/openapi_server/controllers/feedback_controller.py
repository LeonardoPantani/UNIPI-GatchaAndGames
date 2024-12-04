############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import connexion
from flask import jsonify
from pybreaker import CircuitBreaker

from openapi_server.controllers.feedback_internal_controller import submit_feedback
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_string_input

SERVICE_TYPE = "admin"
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)


def feedback_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def post_feedback(string=None, session=None):
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    # valid json request
    feedback_request = connexion.request.args.get("string")
    if len(feedback_request) == 0:
        return jsonify({"message": "Invalid request."}), 400

    feedback_request = sanitize_string_input(feedback_request)

    feedback = {"content": feedback_request}

    response = submit_feedback(feedback, None, session["uuid"])
    if response[1] != 201:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    return jsonify({"message": "Feedback successfully submitted."}), 201
