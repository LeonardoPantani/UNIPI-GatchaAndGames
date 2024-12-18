import bcrypt
import connexion
import requests
from flask import current_app, jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.controllers.profile_internal_controller import (
    delete_profile_by_uuid, exists_profile, edit_username, get_profile
)
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_email_input, sanitize_uuid_input
from openapi_server.helpers.logging import send_log
from openapi_server.models.delete_profile_request import DeleteProfileRequest
from openapi_server.models.edit_profile_request import EditProfileRequest

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])


SERVICE_TYPE = "profile"

FEEDBACK_SERVICE_URL = "https://service_feedback"
CURRENCY_SERVICE_URL = "https://service_currency"
INVENTORY_SERVICE_URL = "https://service_inventory"
AUCTION_SERVICE_URL = "https://service_auction"
PVP_SERVICE_URL = "https://service_pvp"
AUTH_SERVICE_URL = "https://service_auth"
PROFILE_SERVICE_URL = "https://service_profile"


def profile_health_check_get():
    return jsonify({"message": "Service operational."}), 200


@circuit_breaker
def delete_profile():
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    try:
        delete_request = DeleteProfileRequest.from_dict(connexion.request.get_json())
    except Exception:
        return jsonify({"error": "Invalid request"}), 400

    # Verify password
    @circuit_breaker
    def verify_password():
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/internal/get_hashed_password",
            params={"uuid": session.get("uuid")},
            verify=False,
            timeout=current_app.config["requests_timeout"],
        )
        response.raise_for_status()
        stored_hash = response.json()["password"]

        # Compare provided password with stored hash
        if not bcrypt.checkpw(delete_request.password.encode("utf-8"), stored_hash.encode("utf-8")):
            return False
        return True

    if not verify_password():
        send_log(f"delete_profile: Wrong password inserted for user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Invalid password"}), 401
    
    try:
        # 1. Delete user feedbacks
        @circuit_breaker
        def delete_user_feedbacks():
            feedback_response = requests.delete(
                f"{FEEDBACK_SERVICE_URL}/feedback/internal/delete_user_feedbacks",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            feedback_response.raise_for_status()

        delete_user_feedbacks()

    except requests.HTTPError as e:
        send_log(f"delete_user_feedbacks: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"delete_user_feedbacks: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"delete_user_feedbacks: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        # 2. Delete currency transactions
        @circuit_breaker
        def delete_currency_transactions():
            currency_response = requests.delete(
                f"{CURRENCY_SERVICE_URL}/currency/internal/delete_user_transactions",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            currency_response.raise_for_status()

        delete_currency_transactions()

    except requests.HTTPError as e:
        send_log(f"delete_currency_transactions: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"delete_currency_transactions: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"delete_currency_transactions: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        # 3. Get user items
        @circuit_breaker
        def get_user_items():
            inventory_response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/get_items_by_owner_uuid",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            inventory_response.raise_for_status()
            return inventory_response.json()

        item_uuids = get_user_items()

    except requests.HTTPError as e:
        send_log(f"get_user_items: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"get_user_items: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"get_user_items: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        # 4. Refund bidders
        if item_uuids:

            @circuit_breaker
            def refund_bidders():
                refund_response = requests.post(
                    f"{AUCTION_SERVICE_URL}/auction/internal/refund_bidders",
                    json=item_uuids,
                    verify=False,
                    timeout=current_app.config["requests_timeout"],
                )
                refund_response.raise_for_status()

            refund_bidders()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"refund_bidders: Some user was not found when refunding auctions of user: {session['username']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        else:
            send_log(f"refund_bidders: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"refund_bidders: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"refund_bidders: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        # 5. Reset current bidder
        @circuit_breaker
        def reset_current_bidder():
            reset_bidder_response = requests.post(
                f"{AUCTION_SERVICE_URL}/auction/internal/reset_current_bidder",
                params={"uuid": session.get("uuid")},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            reset_bidder_response.raise_for_status()

        reset_current_bidder()

    except requests.HTTPError as e:
        if e.response.status_code != 304:
            send_log(f"reset_current_bidder: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"reset_current_bidder: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"reset_current_bidder: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        # 6. Remove PVP matches
        @circuit_breaker
        def remove_pvp_matches():
            pvp_response = requests.delete(
                f"{PVP_SERVICE_URL}/pvp/internal/remove_by_user_uuid",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            pvp_response.raise_for_status()

        remove_pvp_matches()

    except requests.HTTPError as e:
        send_log(f"remove_pvp_matches: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"remove_pvp_matches: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"remove_pvp_matches: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
       
    try:
        # 7. Remove auctions
        if item_uuids:

            @circuit_breaker
            def remove_auctions():
                auction_response = requests.post(
                    f"{AUCTION_SERVICE_URL}/auction/internal/remove_by_item_uuid",
                    json=item_uuids,
                    verify=False,
                    timeout=current_app.config["requests_timeout"],
                )
                auction_response.raise_for_status()

            remove_auctions()
    except requests.HTTPError as e:
        if e.response.status_code != 304:
            send_log(f"remove_auctions: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"remove_auctions: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"remove_auctions: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    try:

        # 8. Delete inventory
        @circuit_breaker
        def delete_user_inventory():
            delete_inventory_response = requests.delete(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/delete_user_inventory",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            delete_inventory_response.raise_for_status()

        delete_user_inventory()

    except requests.HTTPError as e:
        send_log(f"delete_user_inventory: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"delete_user_inventory: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"delete_user_inventory: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    try:
        # 9. Delete profile
        delete_profile_response = delete_profile_by_uuid(None, session.get("uuid"))
        if delete_profile_response[1] != 200:
            return jsonify({"message": "Error deleting profile"}), delete_profile_response.status_code

        # 10. Delete auth user
        @circuit_breaker
        def delete_auth_user():
            delete_auth_response = requests.delete(
                f"{AUTH_SERVICE_URL}/auth/internal/delete_user_by_uuid",
                params={"uuid": session.get("uuid"), "session": None},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            delete_auth_response.raise_for_status()

        delete_auth_user()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"delete_auth_user: No user found with uuid: {session['uuid']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        else:
            send_log(f"delete_auth_user: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"delete_auth_user: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"delete_auth_user: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    ### Invalidation of token for user uuid = session.get("uuid")... 
    try:

        @circuit_breaker
        def make_request_to_auth_service():
            params = {"uuid": session.get("uuid")}
            url = "https://service_auth/auth/internal/token/invalidate"
            response = requests.delete(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_auth_service()
        
    except requests.HTTPError as e:
        if e.response.status_code == 404: # user not logged in, no need to invalidate session
            send_log(f"make_request_to_auth_service: User with uuid '{session.get("uuid")} is not logged in, strange since they have called this function themselves.", level="info")
        else:
            send_log(f"make_request_to_auth_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_auth_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_auth_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    ## end of token invalidation

    return jsonify({"message": "User profile and related data deleted successfully."}), 200


@circuit_breaker
def edit_profile():
    # Auth verification
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    try:
        edit_request = EditProfileRequest.from_dict(connexion.request.get_json())
    except Exception:
        return jsonify({"error": "Invalid request."}), 400

    # Verify password before proceeding with edit
    @circuit_breaker
    def verify_password():
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/internal/get_hashed_password",
            params={"uuid": session.get("uuid")},
            verify=False,
            timeout=current_app.config["requests_timeout"],
        )
        response.raise_for_status()
        stored_hash = response.json()["password"]

        # Compare provided password with stored hash
        if not bcrypt.checkpw(edit_request.password.encode("utf-8"), stored_hash.encode("utf-8")):
            return False
        return True

    if not verify_password():
        send_log(f"edit_profile: Wrong password inserted for user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Invalid password"}), 401

    user_uuid = session["uuid"]

    # Check if profile exists
    response = exists_profile(None, user_uuid)
    if response[1] != 200:
        send_log(f"exists_profile: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    if not response[0].get_json()["exists"]:
        return jsonify({"error":"User not found"}), 404
    
    # Update email if provided
    if edit_request.email:
        valid, email = sanitize_email_input(edit_request.email)
        if not valid:
            return jsonify({"error": "Invalid input."}), 400
        try:
            @circuit_breaker
            def update_email():
                response = requests.post(
                    f"{AUTH_SERVICE_URL}/auth/internal/edit_email",
                    params={"uuid": user_uuid, "email": email},
                    verify=False,
                    timeout=current_app.config["requests_timeout"],
                )
                response.raise_for_status()
                return response

            result1 = update_email()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                send_log(f"update_email: No user found with uuid: {session['uuid']}.", level="info", service_type=SERVICE_TYPE)
                return jsonify({"error": "User not found"}), 404
            else:
                send_log(f"update_email: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException as e:
            send_log(f"update_email: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            send_log(f"update_email: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        # Update username if provided
    if edit_request.username:

        result2 = edit_username(None, session['uuid'],edit_request.username)

        if result2[1] == 404:
            send_log(f"edit_username: No user found with uuid: {session['uuid']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        elif result2[1] == 409:
            send_log(f"edit_username: User {session['username']} tried to change its username to {edit_request.username}, but it's already taken.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Username already taken."}), 409
        elif result2[1] == 304 and result1.status_code == 304:
            return jsonify({"error": "No changes detected"}), 304
        elif result2[1] != 200:
            send_log(f"edit_username: HttpError {result2} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

        ### Invalidation of token for user uuid = user_uuid...
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
            send_log(f"make_request_to_auth_service: User with uuid '{user_uuid} is not logged in, strange since they have called this function themselves.", level="info")
        else:
            send_log(f"make_request_to_auth_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_auth_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_auth_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    ## end of token invalidation

    send_log(f"edit_profile: User {session['username']} has successfully updated its profile.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message": "Profile updated successfully. Please re-authenticate."}), 200


def get_user_info(uuid):
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    valid, uuid = sanitize_uuid_input(uuid)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    response = get_profile(None, uuid)

    if response[1] == 404:
        send_log(f"get_profile: No user found with uuid: {uuid}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "User not found."}), 404
    elif response[1] != 200:
        send_log(f"get_profile: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    send_log(f"get_user_info: User {session['username']} has successfully gotten profile info of user with uuid {uuid}.", level="general", service_type=SERVICE_TYPE)
    return response