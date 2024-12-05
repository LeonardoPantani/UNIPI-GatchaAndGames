import json
import random
import uuid
from datetime import datetime, timedelta

import connexion
import requests
from flask import current_app, jsonify, request, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from openapi_server.controllers.gacha_internal_controller import get_gacha, list_gachas, exists_pool, get_pool, list_pools
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_string_input, sanitize_uuid_input
from openapi_server.helpers.logging import send_log


# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])


def gacha_health_check_get():
    return jsonify({"message": "Service operational."}), 200


SERVICE_TYPE = "gacha"
GACHA_SERVICE_URL = "https://service_gacha"
PROFILE_SERVICE_URL = "https://service_profile"
INVENTORY_SERVICE_URL = "https://service_inventory"


def get_gacha_info(gacha_uuid):
    """Get information about a specific gacha."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    valid, gacha_uuid = sanitize_uuid_input(gacha_uuid)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    response = get_gacha(None, gacha_uuid)

    if response[1] == 404:
        return jsonify({"error": "Gacha not found."}), 404
    elif response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    return response[0], 200


def pull_gacha(pool_id):
    """Pull a random gacha from a specific pool."""

    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    
    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    pool_id = sanitize_string_input(pool_id)

    # Get pool info
    response = get_pool(None, pool_id)

    if response[1] == 404:
        send_log(f"get_pool: No pool found with name {pool_id} by user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Pool not found"}), 404
    elif response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    pool = response[0].get_json()

    try:
        # Check user currency
        @circuit_breaker
        def check_currency():
            response = requests.get(
                f"{PROFILE_SERVICE_URL}/profile/internal/get_currency_from_uuid",
                params={"user_uuid": user_uuid},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            response.raise_for_status()
            return response.json()

        user_currency = check_currency()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"check_currency: No user found with uuid: {session['username']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found"}), 404
        else:
            send_log(f"check_currency: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"check_currency: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"check_currency: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    if user_currency["currency"] < pool["price"]:
        send_log(f"pull_gacha: Not enough credits for user {session['username']} to pull from {pool_id}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Not enough credits"}), 401

    probabilities = [
        pool["probability_common"],
        pool["probability_rare"],
        pool["probability_epic"],
        pool["probability_legendary"],
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
    selected_item = pool["items"][selected_index]

    try:
        # Deduct currency
        @circuit_breaker
        def deduct_currency():
            response = requests.post(
                f"{PROFILE_SERVICE_URL}/profile/internal/add_currency",
                params={"uuid": user_uuid, "amount": -pool["price"]},
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            response.raise_for_status()
            return response

        deduct_currency()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"deduct_currency: No user found with uuid: {session['username']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found"}), 404
        else:
            send_log(f"deduct_currency: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log(f"deduct_currency: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"deduct_currency: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    new_item_uuid = str(uuid.uuid4())

    item_data = {
        "owner_id": user_uuid,
        "item_id": new_item_uuid,
        "gacha_uuid": selected_item,
        "owners_no": 1,
        "price_paid": pool["price"],
        "obtained_date": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        # Add item to inventory
        @circuit_breaker
        def add_to_inventory():

            response = requests.post(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/insert_item",
                json=item_data,
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            response.raise_for_status()
            return response

    except requests.HTTPError as e:
        send_log(f"add_to_inventory: HttpError {e} for item {new_item_uuid} and user {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log(f"add_to_inventory: RequestException {e} for item {new_item_uuid} and user {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"add_to_inventory: Circuit breaker is open for item {new_item_uuid} and user {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    response = get_gacha(None, selected_item)
    if response[1] == 404:
        return response
    elif response[1] == 503 or response[1] == 400:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    add_to_inventory()

    response_data = response[0].get_json()
    image_url = f"https://localhost/cdn/image/{response_data["gacha_uuid"]}"
    
    send_log(f"pull_gacha: User {session['username']} has successfully pulled gacha {response_data["gacha_uuid"]}, added as item {new_item_uuid}.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"gacha": response_data, "image": image_url})

def get_pool_info():
    """Returns a list of available gacha pools."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    response = list_pools()

    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    return response


def get_gachas(not_owned):  
    """Returns a list of gacha items based on ownership filter."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

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
                verify=False,
                timeout=current_app.config["requests_timeout"],
            )
            response.raise_for_status()
            return response.json()

        owned_gachas = get_owned_gachas()
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No gachas found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    print(owned_gachas)
    # Then get filtered gacha list
    response = list_gachas(owned_gachas, None, not_owned)
    print(response)
    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    return response[0]

