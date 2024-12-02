############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import connexion
import requests
import datetime
from flask import jsonify, current_app
from mysql.connector.errors import (
    DatabaseError,
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.helpers.input_checks import sanitize_uuid_input
from openapi_server.models.feedback_preview import FeedbackPreview
from openapi_server.models.feedback_with_username import (
    FeedbackWithUsername,
)
from openapi_server.models.submit_feedback_request import (
    SubmitFeedbackRequest,
)

MOCK_COUNT = 3
MOCK_FEEDBACKS = [
    (1, 'e3b0c442-98fc-1c14-b39f-92d1282048c0', 'Yare yare daze... Great game!', datetime.datetime(2024, 1, 10, 12, 0)),
    (2, '87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09', 'WRYYYYY! Amazing stands!', datetime.datetime(2024, 1, 11, 13, 30)),
    (3, 'a4f0c592-12af-4bde-aacd-94cd0f27c57e', 'This is... Requiem. Awesome gameplay.', datetime.datetime(2024, 1, 12, 15, 45))
]
MOCK_USERNAME = { 'username': 'DIOBrando' }

SERVICE_TYPE="feedback"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def delete_user_feedbacks(session=None, uuid=None):
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def delete_feedbacks():
            global MOCK_FEEDBACKS
            MOCK_FEEDBACKS = [feedback for feedback in MOCK_FEEDBACKS if feedback[1] != uuid]
            return True

        delete_feedbacks()

        return "", 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def feedback_info(session=None, feedback_id=None):
    if not feedback_id:
        return "", 400
    
    try:
        @circuit_breaker
        def get_feedback():
            global MOCK_FEEDBACKS
            return next((feedback for feedback in MOCK_FEEDBACKS if feedback[0] == feedback_id), None)

        feedback = get_feedback()

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503

    if not feedback:
        return jsonify({"error":"Feedback not found."}), 404
    
    try:
        @circuit_breaker
        def make_request_to_profile_service():
            return MOCK_USERNAME
        
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


def feedback_list(session=None, page_number=None):
    if not page_number:
        return "", 400
    
    items_per_page = 10
    offset = (page_number - 1) * items_per_page
    
    try:
        @circuit_breaker
        def get_feedbacks():
            global MOCK_FEEDBACKS
            return MOCK_FEEDBACKS

        feedback_list = get_feedbacks()

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503

    response = []
    for feedback in feedback_list:
        payload = {
            "id": feedback[0],
            "user_uuid": feedback[1],
            "timestamp": feedback[3]
        }
        response.append(payload)

    return jsonify(response), 200


def submit_feedback(submit_feedback_request=None, session=None, user_uuid=None):
    
    if submit_feedback_request is not None:
        feedback_content = submit_feedback_request.get('content')
    else:
        if not connexion.request.is_json:
            return "", 400
        
        if not user_uuid:
            return "", 400
        
        if not sanitize_uuid_input(user_uuid):
            return "", 400
        
        submit_feedback_request = SubmitFeedbackRequest.from_dict(connexion.request.get_json())
        feedback_content = submit_feedback_request.content
        

    try:
        @circuit_breaker
        def insert_feedback():
            global MOCK_COUNT
            global MOCK_FEEDBACKS

            MOCK_COUNT = MOCK_COUNT + 1
            MOCK_FEEDBACKS.append(
                (MOCK_COUNT, user_uuid, feedback_content, datetime.datetime.now())
            )
            return True
        
        insert_feedback()

        return jsonify({"message":"Feedback added."}), 201

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503