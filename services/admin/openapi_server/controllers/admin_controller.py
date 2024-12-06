import json
import uuid
from datetime import datetime

import connexion
import requests
from flask import current_app, jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server import util
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import (
    sanitize_auction_input,
    sanitize_email_input,
    sanitize_gacha_input,
    sanitize_pagenumber_input,
    sanitize_pool_input,
    sanitize_string_input,
    sanitize_uuid_input,
)
from openapi_server.helpers.logging import query_logs, send_log
from openapi_server.models.auction import Auction
from openapi_server.models.feedback_preview import FeedbackPreview
from openapi_server.models.feedback_with_username import FeedbackWithUsername
from openapi_server.models.gacha import Gacha
from openapi_server.models.get_user_history200_response import GetUserHistory200Response
from openapi_server.models.log import Log
from openapi_server.models.pool import Pool
from openapi_server.models.user_full import UserFull

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

SERVICE_TYPE = "admin"


def admin_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def ban_profile(user_uuid):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    valid, user_uuid = sanitize_uuid_input(user_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    if session["uuid"] == user_uuid:
        return jsonify({"error": "You cannot delete your account like this."}), 406

    try:

        @circuit_breaker
        def make_request_to_feedback_service():
            params = {"uuid": user_uuid}
            url = "https://service_feedback/feedback/internal/delete_user_feedbacks"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_feedback_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        return jsonify({"error": f"Service temporarily unavailable. Please try again later. [RequestError]{e}"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_currency_service():
            params = {"uuid": user_uuid}
            url = "https://service_currency/currency/internal/delete_user_transactions"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_currency_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"uuid": user_uuid}
            url = "https://service_inventory/inventory/internal/get_items_by_owner_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_items = make_request_to_inventory_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_auction_service():
            url = "https://service_auction/auction/internal/refund_bidders"
            response = requests.post(url, json=user_items, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auction_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_auction_service():
            params = {"uuid": user_uuid}
            url = "https://service_auction/auction/internal/reset_current_bidder"
            response = requests.post(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_auction_service()

    except requests.HTTPError as e:
        if e.response.status_code == 304:
            pass
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": f"Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_pvp_service():
            params = {"uuid": user_uuid}
            url = "https://service_pvp/pvp/internal/remove_by_user_uuid"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_pvp_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_auction_service():
            url = "https://service_auction/auction/internal/remove_by_item_uuid"
            response = requests.post(url, json=user_items, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auction_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"uuid": user_uuid}
            url = "https://service_inventory/inventory/internal/delete_user_inventory"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_inventory_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": user_uuid}
            url = "https://service_profile/profile/internal/delete_profile_by_uuid"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": user_uuid}
            url = "https://service_auth/auth/internal/delete_user_by_uuid"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    ### Invalidation of token for user uuid = user_uuid...
    # we ignore 404 error since it means that the user is not logged, good for them.
    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": user_uuid}
            url = "https://service_auth/auth/internal/token/invalidate"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auth_service()
        
    except requests.HTTPError as e:
        if e.response.status_code == 404: # user not logged in, no need to invalidate session
            send_log(f"User with uuid '{session.get("uuid")} is not logged in. No need to invalidate session.", level="info")
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log("RequestException Error.", level="error")
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error.", level="warning")
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    ## end of token invalidation

    return jsonify({"message": "Profile deleted."}), 200


def create_gacha():
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    # valid request from now on
    gacha = Gacha.from_dict(connexion.request.get_json()).to_dict()

    new_uuid = str(uuid.uuid4())
    gacha["gacha_uuid"] = new_uuid

    gacha = sanitize_gacha_input(gacha)

    if not gacha:
        return jsonify({"error": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            url = "https://service_gacha/gacha/internal/gacha/create"
            response = requests.post(url, json=gacha, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Gacha created with uuid: " + new_uuid}), 201


def delete_gacha(gacha_uuid):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    valid, gacha_uuid = sanitize_uuid_input(gacha_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            params = {"uuid": gacha_uuid}
            url = "https://service_gacha/gacha/internal/gacha/delete"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Gacha deleted."}), 200


def create_pool():
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    pool = Pool.from_dict(connexion.request.get_json())

    pool = sanitize_pool_input(pool.to_dict())

    if not pool:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            url = "https://service_gacha/gacha/internal/pool/create"
            response = requests.post(url, json=pool, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Pool created."}), 201


def delete_pool(pool_id):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    pool_id = sanitize_string_input(pool_id)

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            params = {"codename": pool_id}
            url = "https://service_gacha/gacha/internal/pool/delete"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Pool deleted."}), 200


def edit_user_profile(user_uuid, email=None, username=None):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not username and not email:
        return jsonify({"message": "No changes applied."}), 304

    valid, email = sanitize_email_input(email)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    valid, user_uuid = sanitize_uuid_input(user_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": user_uuid}
            url = "https://service_profile/profile/internal/exists"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        exist_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if exist_data["exists"] == False:  # noqa: E712
        return jsonify({"error": "User not found."}), 404

    if email:
        try:

            @circuit_breaker
            def make_request_to_auth_service():
                params = {"uuid": user_uuid, "email": email}
                url = "https://service_auth/auth/internal/edit_email"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()

            make_request_to_auth_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            elif e.response.status_code == 304:
                pass
            elif e.response.status_code == 409: # cant update email since it is already in use
                return jsonify({"error": "That email is already in use."}), 409
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    if username:
        try:

            @circuit_breaker
            def make_request_to_profile_service():
                params = {"uuid": user_uuid, "username": username}
                url = "https://service_profile/profile/internal/edit_username"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()

            make_request_to_profile_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            elif e.response.status_code == 409: # cant update username since it is taken
                return jsonify({"error": "That username is already taken."}), 409
            elif e.response.status_code == 304:
                pass
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


    ### Invalidation of token for user uuid = user_uuid...
    # we ignore 404 error since it means that the user is not logged, good for them.
    try:

        @circuit_breaker
        def make_request_to_auth_service_2():
            params = {"uuid": user_uuid}
            url = "https://service_auth/auth/internal/token/invalidate"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auth_service_2()
        
    except requests.HTTPError as e:
        if e.response.status_code == 404: # user not logged in, no need to invalidate session
            send_log(f"User with uuid '{user_uuid} is not logged in. No need to invalidate session.", level="info")
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log("RequestException Error.", level="error")
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log("CircuitBreaker Error.", level="warning")
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    ## end of token invalidation

    if session["uuid"] != user_uuid:
        return jsonify({"message": "Profile successfully updated."}), 200
    else:
        return jsonify({"message": "Profile successfully updated. You were also logged out, please re-authenticate."}), 200


def get_all_feedbacks(page_number=None):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not page_number:
        return jsonify({"message": "Invalid request."}), 400

    page_number = sanitize_pagenumber_input(page_number)

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_feedback_service():
            params = {"page_number": page_number}
            url = "https://service_feedback/feedback/internal/list"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        feedback_list = make_request_to_feedback_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify(feedback_list), 200


def get_all_profiles(page_number=None):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not page_number:
        return jsonify({"message": "Invalid request."}), 400

    page_number = sanitize_pagenumber_input(page_number)

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"page_number": page_number}
            url = "https://service_profile/profile/internal/list"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        profile_list = make_request_to_profile_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify(profile_list), 200


def get_feedback_info(feedback_id=None):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not feedback_id:
        return jsonify({"message": "Invalid request."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_feedback_service():
            params = {"feedback_id": feedback_id}
            url = "https://service_feedback/feedback/internal/info"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        feedback = make_request_to_feedback_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error":"Feedback not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify(feedback), 200


def get_system_logs():
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    service_type = connexion.request.args.get("service_type")
    endpoint = connexion.request.args.get("endpoint")
    interval = connexion.request.args.get("interval", default=3600, type=int)
    level = connexion.request.args.get("level", default="info")
    start_time = connexion.request.args.get("start_time", type=int)

    if interval < 1 or interval > 2595600:
        return jsonify({"error": "Invalid input."}), 400

    if start_time and start_time > int(datetime.now().timestamp()):
        return jsonify({"error": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    logs = query_logs(service_type, endpoint, interval, level, start_time)

    return jsonify(logs), 200


def get_user_history(user_uuid, history_type, page_number=None):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not user_uuid or not history_type or not page_number:
        return jsonify({"message": "Invalid request."}), 400

    valid, user_uuid = sanitize_uuid_input(user_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    page_number = sanitize_pagenumber_input(page_number)

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_currency_service():
            params = {"uuid": user_uuid, "history_type": history_type, "page_number": page_number}
            url = "https://service_currency/currency/internal/get_user_history"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        transaction_list = make_request_to_currency_service()

    except requests.HTTPError as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        return jsonify({"error": f"Service temporarily unavailable. Please try again later. [RequestError]{e}"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify(transaction_list), 200


def update_auction(auction_uuid):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not auction_uuid:
        return jsonify({"error": "Invalid request."}), 400

    if not connexion.request.is_json:
        return jsonify({"error": "Invalid request."}), 400

    auction = Auction.from_dict(connexion.request.get_json())

    valid, auction_uuid = sanitize_uuid_input(auction_uuid)
    if not valid:
        return jsonify({"error": "Invalid request."}), 400

    auction = sanitize_auction_input(auction.to_dict())
    if not auction:
        return jsonify({"error": "Invalid input."}), 400

    if auction["auction_uuid"] != auction_uuid:
        return jsonify({"message": "Auction UUID in request is different from the one inside the auction object."}), 406

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_auction_service():
            url = "https://service_auction/auction/internal/update"
            response = requests.post(url, json=auction, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_auction_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Auctions not found."}), 404
        elif e.response.status_code == 417:
            return jsonify({"error": "Invalid date format."}), 417
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Auction updated."}), 200


def update_gacha(gacha_uuid):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not gacha_uuid:
        return jsonify({"message": "Invalid request."}), 400

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    gacha = Gacha.from_dict(connexion.request.get_json())

    gacha = sanitize_gacha_input(gacha.to_dict())

    valid, gacha_uuid = sanitize_uuid_input(gacha_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    if gacha["gacha_uuid"] != gacha_uuid:
        return jsonify({"message": "Gacha UUID in request is different from the one inside the gacha object."}), 406

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            url = "https://service_gacha/gacha/internal/gacha/update"
            response = requests.post(url, json=gacha, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Gacha updated."}), 200


def update_pool(pool_id):
    session = verify_login(
        connexion.request.headers.get("Authorization"), audience_required="private_services", service_type=SERVICE_TYPE
    )
    if session[1] != 200:
        return session
    else:
        session = session[0]

    if not pool_id:
        return jsonify({"message": "Invalid request."}), 400

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    pool = Pool.from_dict(connexion.request.get_json())

    pool_id = sanitize_string_input(pool_id)

    pool = sanitize_pool_input(pool.to_dict())

    if not pool:
        return jsonify({"error": "Invalid input"}), 400

    if pool["codename"] != pool_id:
        return jsonify({"message": "Pool UUID in request is different from the one inside the pool object."}), 406

    if (
        pool["public_name"] is None
        or pool["price"] is None
        or pool["items"] is None
        or pool["probability_legendary"] is None
        or pool["probability_rare"] is None
        or pool["probability_epic"] is None
        or pool["probability_common"] is None
    ):
        return jsonify({"message": "Invalid request."}), 400

    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session["uuid"]}
            url = "https://service_auth/auth/internal/get_role_by_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_role_data = make_request_to_auth_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_role = user_role_data["role"]

    if user_role != "ADMIN":
        return jsonify({"error": "This account is not authorized to perform this action."}), 403

    try:

        @circuit_breaker
        def make_request_to_gacha_service():
            url = "https://service_gacha/gacha/internal/pool/update"
            response = requests.post(url, json=pool, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

        make_request_to_gacha_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Pool updated."}), 200
