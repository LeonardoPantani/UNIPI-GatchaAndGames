import connexion
import json
import requests

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_user_history200_response import GetUserHistory200Response  # noqa: E501
from openapi_server.models.log import Log  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user_full import UserFull  # noqa: E501
from openapi_server import util

from openapi_server.helpers.logging import send_log
from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(
    fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError]
)


def admin_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def ban_profile(user_uuid):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action."}
        ), 403

    if session.get("uuid") == user_uuid:
        return jsonify({"error": "You cannot delete your account like this."}), 406

    
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {"user_uuid": user_uuid}
            url = "http://db_manager:8080/db_manager/admin/ban_user_profile"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Profile successfully banned."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        elif e.response.status_code == 406:
            return jsonify({"error": "Cannot ban a user with the ADMIN role."}), 409
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def create_gacha():
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid request from now on
    gacha = Gacha.from_dict(connexion.request.get_json())
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = connexion.request.get_json()
            url = "http://db_manager:8080/db_manager/admin/create_gacha"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify(
            {"message": "Gacha successfully created.", "gacha_uuid": gacha.gacha_uuid}
        ), 201
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 409:  # conflict
            return jsonify({"error": "The provided gacha uuid is already in use."}), 409
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def delete_gacha(gacha_uuid):  # TODO vanno rimosse le cose nel modo corretto
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = gacha_uuid
            url = "http://db_manager:8080/db_manager/admin/delete_gacha"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Gacha successfully deleted."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found."}), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def create_pool():
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    pool = Pool.from_dict(connexion.request.get_json())

    # check if probabilities are inside the probabilities fields and are floats
    if (
        not isinstance(pool.probabilities.legendary_probability, float)
        or not isinstance(pool.probabilities.rare_probability, float)
        or not isinstance(pool.probabilities.epic_probability, float)
        or not isinstance(pool.probabilities.common_probability, float)
    ):
        return jsonify({"error": "Invalid probabilities field."}), 412

    # check if sum of probabilities is 1
    if (
        pool.probabilities.legendary_probability
        + pool.probabilities.epic_probability
        + pool.probabilities.rare_probability
        + pool.probabilities.common_probability
        != 1
    ):
        return jsonify({"error": "Sum of probabilities is not 1."}), 416

    if pool.price < 1:
        return jsonify({"error": "Price should be a positive number."}), 416

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = connexion.request.get_json()
            url = "http://db_manager:8080/db_manager/admin/create_pool"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_dbmanager()

        return jsonify({"message": "Pool successfully created."}), 201
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Item UUID not found in database."}), 404
        elif e.response.status_code == 409:
            return jsonify({"error": "The provided pool id is already in use."}), 409
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def delete_pool(pool_id):  # TODO controllare dipendenze
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = pool_id
            url = "http://db_manager:8080/db_manager/admin/delete_pool"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Pool successfully deleted."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def edit_user_profile(user_uuid, email=None, username=None):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    payload = {"uuid": user_uuid, "email": email, "username": username}

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/edit_user_profile"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response

        response = make_request_to_dbmanager()
        if response.status_code == 203:
            return jsonify({"message": "No changes to profile applied."}), 304

        return jsonify({"message": "User profile successfully updated."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def get_all_feedbacks(page_number=None):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    # valid json request
    if page_number is None:
        page_number = 1

    payload = {"page_number": page_number}

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/get_all_feedbacks"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response = make_request_to_dbmanager()

        return jsonify(response), 200
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
            }
        ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def get_all_profiles(page_number=None):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    # valid json request
    if page_number is None:
        page_number = 1

    payload = {"page_number": page_number}

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/get_all_profiles"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response = make_request_to_dbmanager()

        return jsonify(response), 200
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
            }
        ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def get_feedback_info(feedback_id=None):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    # valid request from now on
    if feedback_id is None:
        feedback_id = 1

    payload = {"feedback_id": feedback_id}

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/get_feedback_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response = make_request_to_dbmanager()

        return jsonify(response), 200

    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Feedback not found."}), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def get_system_logs():  # TODO
    return "do some magic!"


def get_user_history(user_uuid, history_type, page_number=None):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    # valid request from now on
    if page_number is None:
        page_number = 1
    if history_type is None:
        history_type = "ingame"

    payload = {
        "user_uuid": user_uuid,
        "history_type": history_type,
        "page_number": page_number,
    }

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/get_user_history"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        response = make_request_to_dbmanager()

        return jsonify(response), 200

    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        elif e.response.status_code == 405:
            return jsonify({"error": "Invalid history type."}), 400
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def update_auction(auction_uuid):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    auction = Auction.from_dict(connexion.request.get_json())

    if auction.auction_uuid != auction_uuid:
        return jsonify(
            {
                "message": "Auction UUID in request is different from the one inside the auction object."
            }
        ), 406

    # starting price check
    if auction.starting_price <= 0:
        return jsonify({"error": "Starting price cannot be lower or equal to 0."}), 412

    # starting price check
    if auction.current_bid < 0:
        return jsonify({"error": "Current bid cannot be lower than 0."}), 416

    # Current bid cannot be lower than starting price
    if auction.current_bid < auction.starting_price:
        return jsonify(
            {"error": "Current bid cannot be lower than starting price."}
        ), 401

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = connexion.request.get_json()
            url = "http://db_manager:8080/db_manager/admin/update_auction"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Auction updated."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return json.loads(e.response.text), 404
        elif e.response.status_code == 417:
            return jsonify({"error": "Invalid date format."}), 417
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def update_gacha(gacha_uuid):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    gacha = Gacha.from_dict(connexion.request.get_json())

    if gacha.gacha_uuid != gacha_uuid:
        return jsonify(
            {
                "message": "Gacha UUID in request is different from the one inside the gacha object."
            }
        ), 406

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = connexion.request.get_json()
            url = "http://db_manager:8080/db_manager/admin/update_gacha"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Gacha successfully updated."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return json.loads(e.response.text), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503


def update_pool(pool_id):
    if "username" not in session or session.get("role") != "ADMIN":
        return jsonify(
            {"error": "This account is not authorized to perform this action"}
        ), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    pool = Pool.from_dict(connexion.request.get_json())

    if pool.id != pool_id:
        return jsonify(
            {
                "message": "Pool UUID in request is different from the one inside the pool object."
            }
        ), 406

    
    if pool.probabilities is None or pool.name is None or pool.price is None or pool.items is None or pool.probabilities.legendary_probability is None or pool.probabilities.rare_probability is None or pool.probabilities.epic_probability is None or pool.probabilities.common_probability is None:
        return jsonify({"message": "Invalid request."}), 400

    # check if probabilities are are floats
    if (
        not isinstance(pool.probabilities.legendary_probability, float)
        or not isinstance(pool.probabilities.rare_probability, float)
        or not isinstance(pool.probabilities.epic_probability, float)
        or not isinstance(pool.probabilities.common_probability, float)
    ):
        return jsonify({"error": "Invalid probabilities field."}), 412

    # check if sum of probabilities is 1
    if (
        pool.probabilities.legendary_probability
        + pool.probabilities.epic_probability
        + pool.probabilities.rare_probability
        + pool.probabilities.common_probability
        != 1
    ):
        return jsonify({"error": "Sum of probabilities is not 1."}), 416

    if pool.price < 1:
        return jsonify({"error": "Price should be a positive number."}), 416

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = connexion.request.get_json()
            url = "http://db_manager:8080/db_manager/admin/update_pool"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Pool successfully updated."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return json.loads(e.response.text), 404
        else:  # other errors
            return jsonify(
                {
                    "error": "Service temporarily unavailable. Please try again later. [HTTPError]"
                }
            ), 503
    except (
        requests.RequestException
    ):  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify(
            {"error": "Service unavailable. Please try again later. [RequestError]"}
        ), 503
    except CircuitBreakerError: 
        return jsonify(
            {
                "error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"
            }
        ), 503
