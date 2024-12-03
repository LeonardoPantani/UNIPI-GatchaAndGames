import logging

import bcrypt
import string
import connexion
import requests
from flask import jsonify, current_app
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.logging import send_log
from openapi_server.models.delete_profile_request import DeleteProfileRequest
from openapi_server.models.edit_profile_request import EditProfileRequest
from openapi_server.models.user import User

from openapi_server.helpers.input_checks import sanitize_email_input, sanitize_uuid_input

from openapi_server.controllers.profile_internal_controller import edit_username, get_profile, MOCK_AUCTIONS, MOCK_BUNDLESTRANSACTIONS, MOCK_FEEDBACKS, MOCK_INGAMETRANSACTIONS, MOCK_INVENTORIES, MOCK_PROFILES, MOCK_PVPMATCHES, MOCK_USERS

circuit_breaker = CircuitBreaker(
    fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError]
)

from openapi_server.controllers.profile_internal_controller import (
    delete_profile_by_uuid,
)


SERVICE_TYPE="profile"

def profile_health_check_get():
    return jsonify({"message": "Service operational."}), 200



@circuit_breaker
def delete_profile():
    # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

        try:
            delete_request = DeleteProfileRequest.from_dict(connexion.request.get_json())
        except Exception:
            return jsonify({"error": "Invalid request"}), 400

    session["uuid"] =''.join(char for char in session["uuid"] if char not in string.punctuation)
        
    if session["uuid"] not in MOCK_USERS:
        return jsonify({"error": "User not found"}), 404
    
    # Verify password
    @circuit_breaker
    def verify_password():
        global MOCK_USERS
        stored_hash = MOCK_USERS[session["uuid"]][1]

        # Compare provided password with stored hash
        if not bcrypt.checkpw(delete_request.password.encode("utf-8"), stored_hash.encode("utf-8")):
            return False
        return True

    try:
        if not verify_password():
            return jsonify({"error": "Invalid password"}), 401

        # 1. Delete user feedbacks
        @circuit_breaker
        def delete_user_feedbacks():
            global MOCK_FEEDBACKS
            to_remove = [key for key in MOCK_FEEDBACKS if key[0] == session["uuid"]]
            for key in to_remove:
                del MOCK_FEEDBACKS[key]

        delete_user_feedbacks()

        

        # 2. Delete currency transactions
        @circuit_breaker
        def delete_currency_transactions():
            global MOCK_BUNDLESTRANSACTIONS, MOCK_INGAMETRANSACTIONS

            MOCK_BUNDLESTRANSACTIONS = {
                k: v for k, v in MOCK_BUNDLESTRANSACTIONS.items() if k[0] != session["uuid"]
            }
            MOCK_INGAMETRANSACTIONS = {
                k: v for k, v in MOCK_INGAMETRANSACTIONS.items() if k[0] != session["uuid"]
            }

        delete_currency_transactions()

        

        # 3. Get user items
        @circuit_breaker
        def get_user_items():
            global MOCK_INVENTORIES

            MOCK_INVENTORIES = {
                k: v for k, v in MOCK_INVENTORIES.items() if v[0] != session["uuid"]
            }

        item_uuids = get_user_items()

       

        # 4. Refund bidders
        if item_uuids:
            @circuit_breaker
            def refund_bidders():
                global MOCK_AUCTIONS, MOCK_PROFILES

                for k, v in MOCK_AUCTIONS.items():
                    if v[0] in item_uuids:
                        MOCK_PROFILES[v[3]][1] = MOCK_PROFILES[v[3]][1] + v[2]
            
            refund_bidders()

            

        # 5. Reset current bidder
        @circuit_breaker
        def reset_current_bidder():
            for k, v in MOCK_AUCTIONS.items():
                if v[3] == session["uuid"]:  # Controlla se il campo 3 è uguale all'UUID specificato
                    MOCK_AUCTIONS[k] = (
                        v[0],       # Mantieni invariato item_uuid
                        0,          # Imposta a 0 il campo 2 (starting_price)
                        None,       # Imposta a None il campo 3 (current_bid)
                        None,       # Imposta a None il campo 4 (current_bidder)
                        v[4]        # Mantieni invariato il campo end_time
                    )

        reset_current_bidder()

        

        # 6. Remove PVP matches
        @circuit_breaker
        def remove_pvp_matches():
            global MOCK_PVPMATCHES

            MOCK_PVPMATCHES = {
                k: v for k, v in MOCK_PVPMATCHES.items() if v[0] != session["uuid"] and v[1] != session["uuid"]
            }

        remove_pvp_matches()

        
        try:
        # 7. Remove auctions
            if item_uuids:
                @circuit_breaker
                def remove_auctions():
                    global MOCK_AUCTIONS
                    MOCK_AUCTIONS = {
                        k: v for k, v in MOCK_AUCTIONS.items() if k in item_uuids
                    }

                remove_auctions()
        except requests.HTTPError as e:
            if e.response.status_code == 304:
                pass
            
            

        # 8. Delete inventory
        @circuit_breaker
        def delete_user_inventory():
            global MOCK_INVENTORIES
            MOCK_INVENTORIES = {
                k: v for k, v in MOCK_INVENTORIES.items() if v[0] != session["uuid"]
            }

        delete_user_inventory()

        # 9. Delete profile
        delete_profile_response = delete_profile_by_uuid(None,session.get("uuid"))
        if delete_profile_response[1]!= 200:
            return jsonify({"message": "Error deleting profile"}), delete_profile_response.status_code

        # 10. Delete auth user
        @circuit_breaker
        
        def delete_auth_user():
            global MOCK_USERS
            MOCK_USERS = {
                k: v for k, v in MOCK_USERS.items() if k != session["uuid"]
            }

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
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    
    if session[1] != 200:
        return session
    else:
        
        session = session[0]

    username = session["username"]
    
    if not username:
        return jsonify({"error": "Not logged in."}), 403
    
    try:
        edit_request = EditProfileRequest.from_dict(connexion.request.get_json())
        logging.info(f"Request data: {edit_request}")
    except Exception as e:
        logging.error(f"Error parsing request: {str(e)}")
        return jsonify({"error": "Invalid request."}), 400
    
    session["uuid"] =''.join(char for char in session["uuid"] if char not in string.punctuation)
    if session["uuid"] not in MOCK_USERS:
        return jsonify({"error": "User not found"}), 404
    
    # Verify password
    @circuit_breaker
    def verify_password():
        global MOCK_USERS
        stored_hash = MOCK_USERS[session["uuid"]][1]

        # Compare provided password with stored hash
        if not bcrypt.checkpw(edit_request.password.encode("utf-8"), stored_hash.encode("utf-8")):
            return False
        return True

    try:
        if not verify_password():
            return jsonify({"error": "Invalid password"}), 401
    
        user_uuid = session["uuid"]
        
        
        # Check if profile exists
        @circuit_breaker
        def check_profile_exists():
            global MOCK_PROFILES
            return user_uuid in MOCK_PROFILES


        if not check_profile_exists():
            return jsonify({"error": "Profile not found"}), 404
        

        # Update email if provided
        
        if edit_request.email:
            valid, email = sanitize_email_input(edit_request.email)
            if not valid:
                return jsonify({"error": "Invalid input."}), 400

            @circuit_breaker
            def update_email():
                if user_uuid not in MOCK_USERS:
                    return jsonify({"error": "User not found."}), 404
                
                if email == MOCK_USERS[user_uuid][0]:
                    return jsonify({"error": "No changes applied."}), 304
                
                MOCK_USERS[user_uuid] = (email, MOCK_USERS[user_uuid][1], MOCK_USERS[user_uuid][2])
                return jsonify({"message": "Email updated."}), 200

            result1=update_email()

            
        # Update username if provided
        if edit_request.username:
            @circuit_breaker
            def update_username():
                return edit_username(user_uuid, username)

            result2=update_username()

                
            if result1[1] == 304 and result2[1] == 304:
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
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]


    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403
    
    valid, uuid = sanitize_uuid_input(uuid)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    uuid =''.join(char for char in uuid if char not in string.punctuation)
    try:
        @circuit_breaker
        def get_user_profile():
            return get_profile(user_uuid=uuid)

        profile, code = get_user_profile()
        if code == 404:
            return jsonify({"error": "User not found."}), 404
        if code == 200:
            return profile, code
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503