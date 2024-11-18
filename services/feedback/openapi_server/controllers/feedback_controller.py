import connexion
import uuid
import bcrypt
import logging

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server import util

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL

from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
feedback_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)


def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


@feedback_circuit_breaker
def post_feedback():  # noqa: E501
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid json request
    feedback_request = connexion.request.get_json()["string"]
    if len(feedback_request) == 0:
        return jsonify({"message": "Invalid request."}), 400

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    try:
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
            (session['uuid'], feedback_request)
        )
        connection.commit()
        return jsonify({"message": "Feedback created successfully"}), 200
    except Exception as e:
        logging.error(f"Error while posting feedback: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
