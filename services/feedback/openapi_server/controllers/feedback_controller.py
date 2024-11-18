import connexion
import uuid
import bcrypt
import logging

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError



def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


def post_feedback():  # noqa: E501
    """Invia un feedback.

    Crea un feedback per gli amministratori. # noqa: E501

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    data = request.get_json()
    if not data or 'string' not in data:
        return jsonify({"error": "The 'string' field is required in the JSON body."}), 400

    string = data['string']
    user_uuid = session['uuid']  # Get UUID directly from session

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    try:
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
            (user_uuid, string)
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
