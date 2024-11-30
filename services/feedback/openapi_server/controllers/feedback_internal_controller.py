import connexion
import logging
import requests
from typing import Dict
from typing import Tuple
from typing import Union

from pybreaker import CircuitBreaker, CircuitBreakerError
from flask import jsonify, session

from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.submit_feedback_request import SubmitFeedbackRequest  # noqa: E501
from openapi_server import util

from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def delete_user_feedbacks(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def delete_feedbacks():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                DELETE
                FROM feedbacks
                WHERE user_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            connection.commit()
            cursor.close()

        delete_feedbacks()

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def feedback_info(session=None, feedback_id=None):  # noqa: E501
    if not feedback_id:
        return "", 400
    
    try:
        @circuit_breaker
        def get_feedback():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT id, BIN_TO_UUID(user_uuid), content, timestamp
                FROM feedbacks
                WHERE id = %s
            """

            cursor.execute(query, (feedback_id,))
            
            feedback_data = cursor.fetchone()

            cursor.close()

            return feedback_data

        feedback = get_feedback()

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503

    if not feedback:
        return jsonify({"error":"Feedback not found."}), 404
    
    try:
        @circuit_breaker
        def make_request_to_profile_service():
            params = {"user_uuid": feedback[1]}
            url = "https://service_profile/profile/internal/get_username_from_uuid"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        username_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

    username = username_data['username']

    response = {
        "id": feedback[0],
        "user_uuid": feedback[1],
        "username": username,
        "content": feedback[2],
        "timestamp": feedback[3]
    }

    return jsonify(response), 200


def feedback_list(session=None, page_number=None):  # noqa: E501
    if not page_number:
        return "", 400
    
    items_per_page = 10
    offset = (page_number - 1) * items_per_page
    
    try:
        @circuit_breaker
        def get_feedbacks():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT id, BIN_TO_UUID(user_uuid), timestamp
                FROM feedbacks
                LIMIT %s
                OFFSET %s
            """

            cursor.execute(query, (items_per_page, offset))
            
            feedback_data = cursor.fetchall()

            cursor.close()

            return feedback_data

        feedback_list = get_feedbacks()

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError as e:
        logging.error(f"Query: Generic database error.{e}")
        return "", 503
    except CircuitBreakerError:
        return "", 503

    response = []
    for feedback in feedback_list:
        payload = {
            "id": feedback[0],
            "user_uuid": feedback[1],
            "timestamp": feedback[2]
        }
        response.append(payload)

    return jsonify(response), 200

def submit_feedback(submit_feedback_request=None, session=None, user_uuid=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    if submit_feedback_request is not None:
        feedback_content = submit_feedback_request.get('content')
    else:
        submit_feedback_request = SubmitFeedbackRequest.from_dict(connexion.request.get_json())  # noqa: E501
        feedback_content = submit_feedback_request.content

    try:
        @circuit_breaker
        def insert_feedback():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                INSERT INTO feedbacks
                (user_uuid, content)
                VALUES (UUID_TO_BIN(%s), %s)
            """

            cursor.execute(query, (user_uuid, feedback_content))

            connection.commit()
            cursor.close()
        
        insert_feedback()

        return jsonify({"message":"Feedback added."}), 201

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError as e:
        logging.error(f"Query: Programming error.{e}")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError as e:
        logging.error(f"Query: Integrity error.{e}")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503