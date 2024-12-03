import connexion
from flask import jsonify, current_app
import requests
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_uuid_input

#Import the mocked internal functions (these need to be created)
from openapi_server.controllers.inventory_internal_controller import (
    get_inventory_items_by_owner_uuid as get_inventory_items_internal,
    get_item_by_uuid as get_item_by_uuid_internal,
    remove_item as remove_item_internal,
)

SERVICE_TYPE = "inventory"
INVENTORY_SERVICE_URL = "https://service_inventory"  # Placeholder - not used in mocks
AUCTIONS_SERVICE_URL = "https://service_auction"  # Placeholder - not used in mocks

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])


def inventory_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def get_inventory():
    """Returns a list of gacha items currently owned by the player."""
    
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session["uuid"]
    valid, user_uuid=sanitize_uuid_input(user_uuid)

    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    page_number = connexion.request.args.get('page_number', default=1, type=int)    

    try:
        @circuit_breaker
        def get_inventory_items():
            print(user_uuid)
            inventory_items, internal_status_code = get_inventory_items_internal(uuid=user_uuid, page_number=page_number)
            if internal_status_code != 200:
                raise requests.HTTPError(f"Internal service error: {internal_status_code}", response=type('MockResponse', (object,), {'status_code': internal_status_code})())
            return inventory_items
            

        inventory_items = get_inventory_items()
        return inventory_items, 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No items found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    except Exception as e: # Catch other potential errors during processing
        return jsonify({"error": str(e)}), 503


def get_inventory_item_info(inventory_item_id):
    # Auth verification (replace with your mock verify_login call)
    session_data, status_code = verify_login("Bearer test_token", SERVICE_TYPE) # Example - replace "test_token"
    if status_code != 200:
        return session_data, status_code
    user_uuid = session_data.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    valid, inventory_item_id = sanitize_uuid_input(inventory_item_id)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    # Call the mocked internal function
    try:
        item_info, status_code = get_item_by_uuid_internal(inventory_item_id)
        if item_info is None:
             return jsonify({"error": "Item not found"}), 404
        elif item_info.get('owner_id') != user_uuid:
            return jsonify({"error": "Not authorized to access this item"}), 403
        return jsonify(item_info), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 503



def remove_inventory_item():
    # Auth verification (replace with your mock verify_login call)
    session_data, status_code = verify_login("Bearer test_token", SERVICE_TYPE) # Example - replace "test_token"
    if status_code != 200:
        return session_data, status_code
    user_uuid = session_data.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    item_uuid = connexion.request.args.get('inventory_item_id')
    if not item_uuid:
        return jsonify({"error": "Missing item_uuid parameter"}), 400

    valid, item_uuid = sanitize_uuid_input(item_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    # Mock the auction check (replace with your actual mock)
    auction_check = {"found": False} # Example - set "found" to True to simulate item in auction

    if auction_check.get("found", False):
        return jsonify({"error": "Cannot remove item that is currently in auction"}), 400

    # Call the mocked internal function
    try:
        response = remove_item_internal(None, item_uuid, user_uuid) #Call to mocked internal function
        if response[1] == 404:
            return jsonify({"error": "Item not found."}), 404
        elif response[1] != 200:
            return jsonify({"error": "Service unavailable. Please try again later."}), 503

        return jsonify({"message": "Item removed from inventory."}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 503