import traceback
import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import session, jsonify
from openapi_server.helpers.logging import send_log
import logging
import requests

from openapi_server.models.inventory_item import InventoryItem
from openapi_server import util
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.authorization import verify_login
from openapi_server.controllers.inventory_internal_controller import remove_item

SERVICE_TYPE="inventory"
# Service URLs
INVENTORY_SERVICE_URL = "https://service_inventory"
AUCTIONS_SERVICE_URL = "https://service_auctions"

# Circuit breaker instance for inventory operations
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])

def inventory_health_check_get():
    return jsonify({"message": "Service operational."}), 200

def get_inventory():
    """Returns a list of gacha items currently owned by the player."""
    # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403
    
    page_number = connexion.request.args.get('page_number', default=1, type=int)
    
    try:
        @circuit_breaker
        def get_inventory_items():
            response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/list_inventory_items",
                params={
                    "uuid": user_uuid,
                    "page_number": page_number,
                    "session": None
                },
                verify=False
            )
            response.raise_for_status()
            return response.json()

        inventory_items = get_inventory_items()
        return jsonify(inventory_items), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No items found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_inventory_item_info(inventory_item_id):
    """Returns information about a specific inventory item owned by the player."""
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
        def get_item_info():
            response = requests.get(
                f"{INVENTORY_SERVICE_URL}/inventory/internal/get_by_item_uuid",
                params={
                    "uuid": inventory_item_id
                },
                verify=False
            )
            response.raise_for_status()
            return response.json()

        item_info = get_item_info()
        return jsonify(item_info), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def remove_inventory_item():
    """Remove an item from user's inventory."""
    # Auth verification
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    # Get item_uuid from request args
    item_uuid = connexion.request.args.get('inventory_item_id')
    if not item_uuid:
        return jsonify({"error": "Missing item_uuid parameter"}), 400
    
    try:
        # First check if item is in auction     
        @circuit_breaker
        def check_auction_status():
            params = {"uuid": item_uuid}
            url = "http://service_auction:8080/auction/internal/is_open_by_item_uuid"
            response = requests.get(url,params=params, verify=False)
            response.raise_for_status()
            return response.json()
        
        auction_check = check_auction_status()
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    if auction_check.get("found", False):
        return jsonify({"error": "Cannot remove item that is currently in auction"}), 400
    
    response = remove_item(None, item_uuid, user_uuid)

    if response[1] == 404:
        return jsonify({"error": "Item not found."}), 404
    elif response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    
    return jsonify({"message":"Item removed from inventory."}), 200