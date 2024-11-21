import connexion
import uuid
import bcrypt
import requests
import json
import logging
from datetime import datetime

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL

from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError

from pybreaker import CircuitBreaker, CircuitBreakerError



circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


# received from feedback_controller
def submit_feedback(submit_feedback_request=None):
    if not connexion.request.is_json:
        return "", 400

    submit_feedback_request = SubmitFeedbackRequest.from_dict(connexion.request.get_json())
    
    # valid json request
    feedback_request = submit_feedback_request.string
    user_uuid = submit_feedback_request.user_uuid

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
                (user_uuid, feedback_request)
            )
            connection.commit()
        
        make_request_to_db()
        return "", 201
        
    except OperationalError: # if connect to db fails means there is an error in the db
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return "", 503