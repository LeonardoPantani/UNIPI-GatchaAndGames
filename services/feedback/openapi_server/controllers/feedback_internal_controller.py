import connexion
import requests
from flask import current_app, jsonify
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
from openapi_server.helpers.input_checks import sanitize_uuid_input
from openapi_server.helpers.logging import send_log
from openapi_server.models.feedback_preview import FeedbackPreview
from openapi_server.models.feedback_with_username import (
    FeedbackWithUsername,
)
from openapi_server.models.submit_feedback_request import (
    SubmitFeedbackRequest,
)

SERVICE_TYPE = "feedback"
circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=5,
    exclude=[
        requests.HTTPError,
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ],
)


def delete_user_feedbacks(session=None, uuid=None):
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

        return "", 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("Feedback_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def feedback_info(session=None, feedback_id=None):
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

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("Feedback_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503

    if not feedback:
        return jsonify({"error": "Feedback not found."}), 404

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"user_uuid": feedback[1]}
            url = "https://service_profile/profile/internal/get_username_from_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        username_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"make_request_to_profile_service: No user found with uuid: {feedback[1]}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        else:
            send_log(f"make_request_to_profile_service: HttpError {e} for uuid {feedback[1]}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_profile_service: RequestException {e} for uuid {feedback[1]}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_profile_service: Circuit breaker is open for uuid {feedback[1]}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    username = username_data["username"]

    response = {
        "id": feedback[0],
        "user_uuid": feedback[1],
        "username": username,
        "content": feedback[2],
        "timestamp": feedback[3],
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

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("Feedback_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503

    response = []
    for feedback in feedback_list:
        payload = {"id": feedback[0], "user_uuid": feedback[1], "timestamp": feedback[2]}
        response.append(payload)

    return jsonify(response), 200


def submit_feedback(submit_feedback_request=None, session=None, user_uuid=None):
    if submit_feedback_request is not None:
        feedback_content = submit_feedback_request.get("content")
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

        return jsonify({"message": "Feedback added."}), 201

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("Feedback_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503
