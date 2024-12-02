import connexion
import requests
import uuid
import random
import logging
import json

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha
from openapi_server.models.pool import Pool
from openapi_server import util

from openapi_server.helpers.logging import send_log
from flask import jsonify, request, session, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import uuid
from datetime import datetime, timedelta
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.authorization import verify_login

from openapi_server.controllers.gacha_internal_controller import get_gacha as get_gacha_info_internal

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])

def gacha_health_check_get():
    return jsonify({"message": "Service operational."}), 200

SERVICE_TYPE="gacha"
GACHA_SERVICE_URL = "https://service_gacha"
PROFILE_SERVICE_URL = "https://service_profile"
INVENTORY_SERVICE_URL = "https://service_inventory"

def get_gacha_info(gacha_uuid):
    """Get information about a specific gacha."""
        # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]
    try:
        @circuit_breaker
        def get_gacha():
            response = requests.get(
                f"{GACHA_SERVICE_URL}/gacha/internal/gacha/get",
                params={"uuid": gacha_uuid},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        gacha_info = get_gacha()
        return jsonify(gacha_info), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    
def pull_gacha(pool_id):
    """Pull a random gacha from a specific pool."""
    
    # Auth verification 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    try:
        # Check if pool exists
        @circuit_breaker
        def check_pool_exists():
            response = requests.get(
                f"{GACHA_SERVICE_URL}/gacha/internal/pool/exists",
                params={"uuid": pool_id},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        pool_exists = check_pool_exists()
        if not pool_exists.get('exists'):
            return jsonify({"error": "Pool not found"}), 404

        # Get pool info
        @circuit_breaker
        def get_pool_info():
            response = requests.get(
                f"{GACHA_SERVICE_URL}/gacha/internal/pool/get",
                params={"uuid": pool_id},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        pool = get_pool_info()
        # Check user currency
        @circuit_breaker
        def check_currency():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/get_currency_from_uuid",
                params={"user_uuid": user_uuid},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        user_currency = check_currency()

        if user_currency['currency'] < pool['price']:
            return jsonify({"error": "Not enough credits"}), 401

        probabilities = [
            pool['probability_common'],
            pool['probability_rare'],
            pool['probability_epic'],
            pool['probability_legendary']
        ]

        # Generate random value between 0 and 1
        roll = random.random()

        # Cumulative probability to determine item
        cumulative_prob = 0
        selected_index = 0

        for i, prob in enumerate(probabilities):
            cumulative_prob += prob
            if roll <= cumulative_prob:
                selected_index = i
                break

        # Get the selected item from pool items list
        selected_item = pool['items'][selected_index]
  


        # Deduct currency
        @circuit_breaker
        def deduct_currency():
            response = requests.post(
                f"{PROFILE_SERVICE_URL}/profile/internal/add_currency",
                params={
                    "uuid": user_uuid,
                    "amount": -pool['price']
                },
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response

        deduct_currency()
        
        # Add item to inventory
        @circuit_breaker
        def add_to_inventory():
            new_item_uuid = str(uuid.uuid4())

            item_data = {
                "owner_id": user_uuid,
                "item_id": new_item_uuid,  
                "gacha_uuid": selected_item,  
                "owners_no": 1,
                "price_paid": pool['price'],
                "obtained_date": datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            response = requests.post(
            f"{INVENTORY_SERVICE_URL}/inventory/internal/insert_item",
            json=item_data,
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response

        response=get_gacha_info_internal(None,selected_item)
        if response[1] == 404:
            return response
        elif response[1] == 503 or response[1] == 400:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

        add_to_inventory()
        return (response)

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_pool_info():
    """Returns a list of available gacha pools."""
    # Auth verification 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    try:
        @circuit_breaker
        def get_pools():
            response = requests.post(
                f"{GACHA_SERVICE_URL}/gacha/internal/pool/list",
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        pools = get_pools()
        return jsonify(pools), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No pools found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_gachas(not_owned):
    """Returns a list of gacha items based on ownership filter."""
    # Auth verification 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    try:
        # First get user's owned gacha types
        @circuit_breaker
        def get_owned_gachas():
            response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/get_gachas_types_of_user",
                params={"user_uuid": user_uuid},
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        owned_gachas = get_owned_gachas()
        print(owned_gachas)
        # Then get filtered gacha list
        @circuit_breaker
        def get_gacha_list():
            response = requests.post(
                f"{GACHA_SERVICE_URL}/gacha/internal/gacha/list",
                json=owned_gachas,
                verify=False, timeout=current_app.config['requests_timeout']
            )
            response.raise_for_status()
            return response.json()

        gacha_list = get_gacha_list()
        return jsonify(gacha_list), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No gachas found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503