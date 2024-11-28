import connexion
import uuid
import requests
import json
import logging
from datetime import datetime

from typing import Dict
from typing import Tuple
from typing import Union
from openapi_server.helpers.logging import send_log
from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server import util

from flask import jsonify, request, session
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.db import get_db



circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


# received from feedback_controller
def submit_feedback(submit_feedback_request=None):
    if not connexion.request.is_json:
        return "", 400

    submit_feedback_request = SubmitFeedbackRequest.from_dict(connexion.request.get_json())
    
    # valid json request
    feedback_request = submit_feedback_request.string
    user_uuid = submit_feedback_request.user_uuid


    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
                (user_uuid, feedback_request)
            )
            connection.commit()
        
        make_request_to_db()
        return "", 201
        
    except OperationalError:
        return "", 500
    except ProgrammingError:
        return "", 500
    except InternalError:
        return "", 500
    except InterfaceError:
        return "", 500
    except DatabaseError:
        return "", 500
    except CircuitBreakerError:
        return "", 503