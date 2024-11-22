import logging
import connexion
import uuid
import bcrypt
import json
import requests
from datetime import date

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction
from openapi_server.models.feedback import Feedback
from openapi_server.models.gacha import Gacha
from openapi_server.models.pool import Pool
from openapi_server.models.user import User
from openapi_server import util

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])



def admin_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def ban_profile(user_uuid):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if session.get('uuid') == user_uuid:
        return jsonify({"error": "You cannot delete your account like this"}), 406
    
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
        elif e.response.status_code == 409: 
            return jsonify({"error": "Cannot ban a user with the ADMIN role."}), 409
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def create_gacha():
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
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

        return jsonify({"message": "Gacha successfully created.", "gacha_uuid": gacha.gacha_uuid}), 201
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 400: # programming error
            return jsonify({"error": "User not found."}), 404
        elif e.response.status_code == 409: # conflict
            return jsonify({"error": "The provided gacha uuid is already in use."}), 409
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def delete_gacha(gacha_uuid): #TODO vanno rimosse le cose nel modo corretto
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
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
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        delete_query = "DELETE FROM gachas_types WHERE uuid = %s"
        cursor.execute(delete_query, (gacha_uuid,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Gacha not found."}), 404

        cursor.close()

        return jsonify({"message": "Gacha successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_pool():  
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    pool = Pool.from_dict(connexion.request.get_json())

    # check if probabilities are inside the probabilities fields and are floats
    if not isinstance(pool.probabilities.legendary_probability, float) or not isinstance(pool.probabilities.rare_probability, float) or not isinstance(pool.probabilities.epic_probability, float) or not isinstance(pool.probabilities.common_probability, float):
        return jsonify({"error": "Invalid probabilities field."}), 412
    
    # check if sum of probabilities is 1
    if pool.probabilities.legendary_probability + pool.probabilities.epic_probability + pool.probabilities.rare_probability + pool.probabilities.common_probability != 1:
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
            return jsonify({"error": "Item UUID not found in database."}), 409
        elif e.response.status_code == 409:
            return jsonify({"error": "The provided pool id is already in use."}), 409
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    

def delete_pool(pool_id): # TODO controllare dipendenze
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "DELETE FROM gacha_pools WHERE codename = %s"
        cursor.execute(query, (pool_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Pool not found."}), 404

        cursor.close()

        return jsonify({"message": "Pool successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def edit_user_profile(user_uuid, email=None, username=None):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    payload = {
        "uuid": user_uuid,
        "email": email,
        "username": username
    }

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/admin/edit_user_profile"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response

        response = make_request_to_dbmanager()
        if response.status_code == 203:
            return jsonify({"message": "No changes to profile applied."}), 203

        return jsonify({"message": "User profile successfully updated."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_all_feedbacks(page_number=None):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid json request
    if page_number is None:
        page_number = 1

    payload = {
        "page_number": page_number
    }

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
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_all_profiles(page_number=None):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
     # valid json request
    if page_number is None:
        page_number = 1

    payload = {
        "page_number": page_number
    }

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
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_feedback_info(feedback_id=None):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    if feedback_id is None:
        feedback_id = 1
    
    payload = {
        "feedback_id": feedback_id
    }

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
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_system_logs(): # TODO
    return 'do some magic!'


def get_user_history(user_uuid, history_type, page_number=None):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    if page_number is None:
        page_number = 1
    if history_type is None:
        history_type = "ingame"
    
    payload = {
        "user_uuid": user_uuid,
        "history_type": history_type,
        "page_number": page_number
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
            return jsonify({"error": "Invalid history type."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def update_auction(auction_uuid):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    
    auction = Auction.from_dict(connexion.request.get_json())
    
    if auction.auction_uuid != auction_uuid:
        return jsonify({"message": "Auction UUID in request is different from the one inside the auction object."}), 406
    
    # starting price check
    if auction.starting_price <= 0:
        return jsonify({"error": "Starting price cannot be lower or equal to 0."}), 412
    
    # starting price check
    if auction.current_bid < 0:
        return jsonify({"error": "Current bid cannot be lower than 0."}), 416
    
    # Current bid cannot be lower than starting price
    if auction.current_bid < auction.starting_price:
        return jsonify({"error": "Current bid cannot be lower than starting price."}), 401
    

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if auction with that uuid exists
        query = "SELECT uuid FROM auctions WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Auction not found"}), 404

        # check if item with that uuid exists
        query = "SELECT item_uuid FROM inventories WHERE item_uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction.inventory_item_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Item ID not found in any inventory"}), 404

        # check if current bidder is a valid user uuid
        query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction.current_bidder,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Current bidder user profile not found"}), 404

        # auction exists, continue
        query = "UPDATE auctions SET item_uuid = UUID_TO_BIN(%s), starting_price = %s, current_bid = %s, current_bidder = UUID_TO_BIN(%s), end_time = %s WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (auction.inventory_item_id, auction.starting_price, auction.current_bid, auction.current_bidder, auction.end_time, auction_uuid))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Auction successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def update_gacha(gacha_uuid):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    gacha = Gacha.from_dict(connexion.request.get_json())

    if gacha.gacha_uuid != gacha_uuid:
        return jsonify({"message": "Gacha UUID in request is different from the one inside the gacha object."}), 406
    
    # check if stats have correct rating and create a map with converted letters to number ratings
    letters_map = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1
    }
    attributes = ['power', 'speed', 'durability', 'precision', 'range', 'potential']
    converted = {}
    for attr in attributes:
        letter = getattr(gacha.attributes, attr)
        if letter in letters_map:
            converted[attr] = letters_map[letter]
        else: # no valid letter found
            converted[attr] = None
    # converted is a map with for each key (stat) a value (numeric of the stat)

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if gacha with that uuid exists
        query = "SELECT uuid FROM gachas_types WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (gacha_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Gacha not found."}), 404
        

        query = "UPDATE gachas_types SET name = %s, stat_power = %s, stat_speed = %s, stat_durability = %s, stat_precision = %s, stat_range = %s, stat_potential = %s, rarity = %s WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (gacha.name, converted["power"], converted["speed"], converted["durability"], converted["precision"], converted["range"], converted["potential"], gacha.rarity, gacha.gacha_uuid))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Gacha successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def update_pool(pool_id):
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    pool = Pool.from_dict(connexion.request.get_json())

    if pool.id != pool_id:
        return jsonify({"message": "Pool UUID in request is different from the one inside the pool object."}), 406

    # check if probabilities are inside the probabilities fields and are floats
    if not isinstance(pool.probabilities.legendary_probability, float) or not isinstance(pool.probabilities.rare_probability, float) or not isinstance(pool.probabilities.epic_probability, float) or not isinstance(pool.probabilities.common_probability, float):
        return jsonify({"error": "Invalid probabilities field."}), 412
    
    # check if sum of probabilities is 1
    if pool.probabilities.legendary_probability + pool.probabilities.epic_probability + pool.probabilities.rare_probability + pool.probabilities.common_probability != 1:
        return jsonify({"error": "Sum of probabilities is not 1."}), 416

    if pool.price < 1:
        return jsonify({"error": "Price should be a positive number."}), 416

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        probabilities = {
            "common": pool.probabilities.common_probability,
            "rare": pool.probabilities.rare_probability,
            "epic": pool.probabilities.epic_probability,
            "legendary":  pool.probabilities.legendary_probability,
        }
        query = "UPDATE gacha_pools SET public_name = %s, probabilities = %s, price = %s WHERE codename = %s"
        cursor.execute(query, (pool.name, json.dumps(probabilities), pool.price, pool_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Pool not found."}), 404
        
        cursor.close()

        return jsonify({"message": "Pool successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
