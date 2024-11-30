import traceback
import connexion
import bcrypt
import logging
import requests

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.delete_profile_request import DeleteProfileRequest
from openapi_server.models.edit_profile_request import EditProfileRequest
from openapi_server.models.user import User
from openapi_server import util
from openapi_server.helpers.logging import send_log

from flask import session, jsonify

from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.authorization import verify_login
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(
    fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError]
)

from openapi_server.controllers.profile_internal_controller import delete_profile_by_uuid

FEEDBACK_SERVICE_URL = "http://service_feedback:8080"
CURRENCY_SERVICE_URL = "http://service_currency:8080"
INVENTORY_SERVICE_URL = "http://service_inventory:8080"
AUCTION_SERVICE_URL = "http://service_auction:8080"
PVP_SERVICE_URL = "http://service_pvp:8080"
AUTH_SERVICE_URL = "http://service_auth:8080"
PROFILE_SERVICE_URL = "http://service_profile:8080"

def profile_health_check_get():
    return jsonify({"message": "Service operational."}), 200



@circuit_breaker
def delete_profile():
    # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'))
    if session[1] != 200:
        return session
    else:
        session = session[0]

    

    try:
        # 1. Delete user feedbacks
        @circuit_breaker
        def delete_user_feedbacks():
            feedback_response = requests.delete(
                f"{FEEDBACK_SERVICE_URL}/feedback/internal/delete_user_feedbacks",
                params={"uuid":session.get("uuid") ,"session": None}
            )
            feedback_response.raise_for_status()

        delete_user_feedbacks()

        

        # 2. Delete currency transactions
        @circuit_breaker
        def delete_currency_transactions():
            currency_response = requests.delete(
                f"{CURRENCY_SERVICE_URL}/currency/internal/delete_user_transactions",
                params={"uuid":session.get("uuid"),"session": None}
            )
            currency_response.raise_for_status()

        delete_currency_transactions()

        

        # 3. Get user items
        @circuit_breaker
        def get_user_items():
            inventory_response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/get_items_by_owner_uuid",
                params={"uuid": session.get("uuid"),"session": None}
            )
            inventory_response.raise_for_status()
            return inventory_response.json()

        item_uuids = get_user_items()

       

        # 4. Refund bidders
        if item_uuids:
            @circuit_breaker
            def refund_bidders():
                refund_response = requests.post(
                    f"{AUCTION_SERVICE_URL}/auction/internal/refund_bidders",
                    json=item_uuids
                )
                refund_response.raise_for_status()
            
            refund_bidders()

            

        # 5. Reset current bidder
        @circuit_breaker
        def reset_current_bidder():
            reset_bidder_response = requests.post(
                f"{AUCTION_SERVICE_URL}/auction/internal/reset_current_bidder",
                params={"uuid": session.get("uuid")}
            )
            reset_bidder_response.raise_for_status()

        reset_current_bidder()

        

        # 6. Remove PVP matches
        @circuit_breaker
        def remove_pvp_matches():
            pvp_response = requests.delete(
                f"{PVP_SERVICE_URL}/pvp/internal/remove_by_user_uuid",
                params={"uuid": session.get("uuid"),"session": None}
            )
            pvp_response.raise_for_status()

        remove_pvp_matches()

        
        try:
        # 7. Remove auctions
            if item_uuids:
                @circuit_breaker
                def remove_auctions():
                    auction_response = requests.post(
                        f"{AUCTION_SERVICE_URL}/auction/internal/remove_by_item_uuid",
                        json=item_uuids
                    )
                    auction_response.raise_for_status()

                remove_auctions()
        except requests.HTTPError as e:
            if e.response.status_code == 304:
                pass
            
            

        # 8. Delete inventory
        @circuit_breaker
        def delete_user_inventory():
            delete_inventory_response = requests.delete(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/delete_user_inventory",
                params={"uuid": session.get("uuid"),"session": None}
            )
            delete_inventory_response.raise_for_status()

        delete_user_inventory()

        # 9. Delete profile
        delete_profile_response = delete_profile_by_uuid(None,session.get("uuid"))
        if delete_profile_response[1]!= 200:
            return jsonify({"message": "Error deleting profile"}), delete_profile_response.status_code

        # 10. Delete auth user
        @circuit_breaker
        def delete_auth_user():
            delete_auth_response = requests.delete(
                f"{AUTH_SERVICE_URL}/auth/internal/delete_user_by_uuid",
                params={"uuid": session.get("uuid"),"session": None}
            )
            delete_auth_response.raise_for_status()

        delete_auth_user()

        return jsonify({"message": "User profile and related data deleted successfully"}), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503




@circuit_breaker
def edit_profile():
    # Auth verification

    session = verify_login(connexion.request.headers.get('Authorization'))
    if session[1] != 200:
        return session
    else:
        session = session[0]

    username = session.get('username')
    if not username:
        return jsonify({"error": "Not logged in."}), 403

    try:
        edit_request = EditProfileRequest.from_dict(connexion.request.get_json())
        logging.info(f"Request data: {edit_request}")
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        return jsonify({"error": "Invalid request."}), 400

    try:
        user_uuid = session.get('uuid')

        # Check if profile exists
        @circuit_breaker
        def check_profile_exists():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/exists",
                params={"uuid": user_uuid}
            )
            response.raise_for_status()
            return response.json()

        if not check_profile_exists():
            return jsonify({"error": "Profile not found"}), 404

        # Update email if provided
        
        if edit_request.email:
            @circuit_breaker
            def update_email():
                response = requests.post(
                    f"{AUTH_SERVICE_URL}/auth/internal/edit_email",
                    params={"uuid": user_uuid, "email": edit_request.email}
                )
                response.raise_for_status()
                return response

            result=update_email()
            if result.status_code == 304:
                return jsonify({"error": "No changes detected"}), 304

            
            # Update username if provided
            if edit_request.username:
                @circuit_breaker
                def update_username():
                    response = requests.post(
                        f"{PROFILE_SERVICE_URL}/profile/internal/edit_username",
                        params={"uuid": user_uuid, "username": edit_request.username}
                    )
                    
                    response.raise_for_status()
                    return response

                result=update_username()
                
                if result.status_code == 304:
                    return jsonify({"error": "No changes detected"}), 304
                session['username'] = edit_request.username
            

            return jsonify({"message": "Profile updated successfully"}), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_user_info(uuid):
 # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'))
    if session[1] != 200:
        return session
    else:
        session = session[0]


    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    try:
        @circuit_breaker
        def get_user_profile():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/get_profile",
                params={"user_uuid": uuid}
            )
            response.raise_for_status()
            return response.json()
            
        profile = get_user_profile()
        return profile, 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503