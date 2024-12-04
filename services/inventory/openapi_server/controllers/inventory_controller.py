import traceback

import connexion
import requests
from flask import current_app, jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server import util
from openapi_server.controllers.inventory_internal_controller import remove_item, get_inventory_items_by_owner_uuid, get_item_by_uuid
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_uuid_input
from openapi_server.helpers.logging import send_log
from openapi_server.models.inventory_item import InventoryItem

SERVICE_TYPE = "inventory"
# Service URLs
INVENTORY_SERVICE_URL = "https://service_inventory"
AUCTIONS_SERVICE_URL = "https://service_auction"

# Circuit breaker instance for inventory operations
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])


def inventory_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def get_inventory():
    """Returns a list of gacha items currently owned by the player."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    page_number = connexion.request.args.get("page_number", default=1, type=int)

    response = get_inventory_items_by_owner_uuid(None, session['uuid'], page_number)

    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    return response


def get_inventory_item_info(inventory_item_id):
    """Returns information about a specific inventory item owned by the player."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    user_uuid = session["uuid"]

    valid, inventory_item_id = sanitize_uuid_input(inventory_item_id)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    response = get_item_by_uuid(None, inventory_item_id)

    if response[1] == 404:
        return jsonify({"error": "Item not found."}), 404
    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    item = response[0].get_json()

    if item["owner_id"] != user_uuid:
        return jsonify({"error": "Not authorized to access this item."}), 403
    
    return response


def remove_inventory_item():
    """Remove an item from user's inventory."""
    # Auth verification
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    # Get item_uuid from request args
    item_uuid = connexion.request.args.get("inventory_item_id")
    owner_id = connexion.request.args.get("inventory_item_owner_id")
    if not item_uuid:
        return jsonify({"error": "Missing item_uuid parameter"}), 400

    valid, item_uuid = sanitize_uuid_input(item_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400
    
    if not owner_id:
        return jsonify({"error": "Missing item_uuid parameter"}), 400

    valid, owner_id = sanitize_uuid_input(owner_id)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400
    
    if owner_id != session['uuid']:
        return jsonify({"error": "Not authorized to access this item."}), 403

    try:
        # First check if item is in auction
        @circuit_breaker
        def check_auction_status():
            params = {"uuid": item_uuid}

            url = f"{AUCTIONS_SERVICE_URL}/auction/internal/is_open_by_item_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()

            return response.json()

        auction_check = check_auction_status()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    if auction_check.get("found", False):
        return jsonify({"error": "Cannot remove item that is currently in auction"}), 400

    response = remove_item(None, item_uuid, session['uuid'])

    if response[1] == 404:
        return jsonify({"error": "Item not found."}), 404
    elif response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    return jsonify({"message": "Item removed from inventory."}), 200
