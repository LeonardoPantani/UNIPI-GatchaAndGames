import connexion
import requests

from flask import jsonify, session
from openapi_server.helpers.logging import send_log
from pybreaker import CircuitBreaker, CircuitBreakerError
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server import util
from openapi_server.helpers.authorization import verify_login


circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)


def feedback_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def post_feedback(string=None, session=None):
    session = verify_login(connexion.request.headers.get('Authorization'))
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione
    

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