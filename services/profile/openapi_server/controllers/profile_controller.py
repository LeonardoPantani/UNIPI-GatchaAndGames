import bcrypt

import connexion
import requests
from flask import jsonify, current_app
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.logging import send_log
from openapi_server.models.delete_profile_request import DeleteProfileRequest
from openapi_server.models.edit_profile_request import EditProfileRequest
from openapi_server.models.user import User
from openapi_server.controllers.profile_internal_controller import (
    delete_profile_by_uuid,
)

from openapi_server.helpers.input_checks import sanitize_email_input, sanitize_uuid_input

circuit_breaker = CircuitBreaker(
    fail_max=5, reset_timeout=5, exclude=[requests.HTTPError]
)



SERVICE_TYPE="profile"

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
            verify=False, timeout=current_app.config['requests_timeout']
        )
        response.raise_for_status()
        stored_hash = response.json()["password"]
        
        # Compare provided password with stored hash
        if not bcrypt.checkpw(delete_request.password.encode('utf-8'), stored_hash.encode('utf-8')):
            return False
        return True

    try:
        if not verify_password():
            return jsonify({"error": "Invalid password"}), 401

        # 1. Delete user feedbacks
        @circuit_breaker
        def delete_user_feedbacks():
            feedback_response = requests.delete(
                f"{FEEDBACK_SERVICE_URL}/feedback/internal/delete_user_feedbacks",
                params={"uuid":session.get("uuid") ,"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            feedback_response.raise_for_status()

        delete_user_feedbacks()

        

        # 2. Delete currency transactions
        @circuit_breaker
        def delete_currency_transactions():
            currency_response = requests.delete(
                f"{CURRENCY_SERVICE_URL}/currency/internal/delete_user_transactions",
                params={"uuid":session.get("uuid"),"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            currency_response.raise_for_status()

        delete_currency_transactions()

        

        # 3. Get user items
        @circuit_breaker
        def get_user_items():
            inventory_response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/get_items_by_owner_uuid",
                params={"uuid": session.get("uuid"),"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
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
                    json=item_uuids,
                verify=False, timeout=current_app.config['requests_timeout']
                )
                refund_response.raise_for_status()
            
            refund_bidders()

            

        # 5. Reset current bidder
        @circuit_breaker
        def reset_current_bidder():
            reset_bidder_response = requests.post(
                f"{AUCTION_SERVICE_URL}/auction/internal/reset_current_bidder",
                params={"uuid": session.get("uuid")},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            reset_bidder_response.raise_for_status()

        reset_current_bidder()

        

        # 6. Remove PVP matches
        @circuit_breaker
        def remove_pvp_matches():
            pvp_response = requests.delete(
                f"{PVP_SERVICE_URL}/pvp/internal/remove_by_user_uuid",
                params={"uuid": session.get("uuid"),"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
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
                        json=item_uuids,
                verify=False, timeout=current_app.config['requests_timeout']
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
                params={"uuid": session.get("uuid"),"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
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
                params={"uuid": session.get("uuid"),"session": None},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            delete_auth_response.raise_for_status()

        delete_auth_user()

        return jsonify({"message": "User profile and related data deleted successfully"}), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


@circuit_breaker
def edit_profile():
    # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    
    if session[1] != 200:
        return session
    else:
        
        session = session[0]

    username = session["username"]
    
    try:
        edit_request = EditProfileRequest.from_dict(connexion.request.get_json())
        logging.info(f"Request data: {edit_request}")
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        return jsonify({"error": "Invalid request."}), 400
    
    # Verify password before proceeding with edit
    @circuit_breaker
    def verify_password():
        response = requests.get(
            f"{AUTH_SERVICE_URL}/auth/internal/get_hashed_password",
            params={"uuid": session.get("uuid")},
            verify=False, timeout=current_app.config['requests_timeout']
        )
        response.raise_for_status()
        stored_hash = response.json()["password"]
        
        # Compare provided password with stored hash
        if not bcrypt.checkpw(edit_request.password.encode('utf-8'), stored_hash.encode('utf-8')):
            return False
        return True

    try:
        if not verify_password():
            return jsonify({"error": "Invalid password"}), 401
    
        user_uuid = session["uuid"]
        
        
        # Check if profile exists
        @circuit_breaker
        def check_profile_exists():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/exists",
                params={"uuid": user_uuid},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        if not check_profile_exists():
            return jsonify({"error": "Profile not found"}), 404
        

        # Update email if provided
        
        if edit_request.email:
            valid, email = sanitize_email_input(edit_request.email)
            if not valid:
                return jsonify({"error": "Invalid input."}), 400

            @circuit_breaker
            def update_email():
                response = requests.post(
                    f"{AUTH_SERVICE_URL}/auth/internal/edit_email",
                    params={"uuid": user_uuid, "email": email},
                verify=False, timeout=current_app.config['requests_timeout']
                )
                response.raise_for_status()
                return response

            result1=update_email()

            
        # Update username if provided
        if edit_request.username:
            @circuit_breaker
            def update_username():
                response = requests.post(
                    f"{PROFILE_SERVICE_URL}/profile/internal/edit_username",
                    params={"uuid": user_uuid, "username": edit_request.username},
                verify=False, timeout=current_app.config['requests_timeout']
                )
                
                response.raise_for_status()
                return response

            result2=update_username()
                
            if result1.status_code == 304 and result2.status_code == 304:
                return jsonify({"error": "No changes detected"}), 304
            session['username'] = edit_request.username
            

        return jsonify({"message": "Profile updated successfully"}), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


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

    try:
        @circuit_breaker
        def get_user_profile():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/get_profile",
                params={"user_uuid": uuid},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()
            
        profile = get_user_profile()
        return profile, 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503