import connexion
import requests
from flask import jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

# Import the mocked internal functions (these need to be created)
from openapi_server.controllers.inventory_internal_controller import (
    get_inventory_items_by_owner_uuid as get_inventory_items_internal,
)
from openapi_server.controllers.inventory_internal_controller import (
    get_item_by_uuid as get_item_by_uuid_internal,
)
from openapi_server.controllers.inventory_internal_controller import (
    remove_item as remove_item_internal,
)
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_uuid_input

SERVICE_TYPE = "inventory"
INVENTORY_SERVICE_URL = "https://service_inventory"  # Placeholder - not used in mocks
AUCTIONS_SERVICE_URL = "https://service_auction"  # Placeholder - not used in mocks

MOCK_AUCTION_DATA = {
    "aabbccdd-eeff-0011-2233-445566778899": {  # Auction 1
        "status": "closed",
        "starting_price": 5000,
        "current_bid": 6000,
        "current_bidder": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "inventory_item_id": "f7e6d5c4-b3a2-9180-7654-321098fedcba",
        "end_time": "2024-02-01 00:00:00",
        "inventory_item_owner_id": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
    },
    "a9b8c7d6-e5f4-3210-9876-fedcba987654": {  # Auction 2 (Speedwagon's item)
        "status": "open",
        "starting_price": 5000,
        "current_bid": 6500,
        "current_bidder": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "inventory_item_id": "c7b6a5d4-e3f2-1098-7654-fedcba987654",
        "end_time": "2024-02-01 00:00:00",
        "inventory_item_owner_id": "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
    },
    "some_other_auction_id": {  # Another auction for Speedwagon (open)
        "status": "open",
        "starting_price": 2000,
        "current_bid": 2500,
        "current_bidder": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "inventory_item_id": "some_other_item_id",
        "end_time": "2024-03-15 12:00:00",
        "inventory_item_owner_id": "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
    },
}

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])


def inventory_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def get_inventory():
    """Returns a list of gacha items currently owned by the player."""

    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session["uuid"]

    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    page_number = connexion.request.args.get("page_number", default=1, type=int)

    try:

        @circuit_breaker
        def get_inventory_items():
            inventory_items, internal_status_code = get_inventory_items_internal(
                uuid=user_uuid, page_number=page_number
            )
            if internal_status_code != 200:
                raise requests.HTTPError(
                    f"Internal service error: {internal_status_code}",
                    response=type("MockResponse", (object,), {"status_code": internal_status_code})(),
                )
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
    except Exception as e:  # Catch other potential errors during processing
        return jsonify({"error": str(e)}), 503


def get_inventory_item_info(inventory_item_id):
    """Returns information about a specific inventory item owned by the player."""
    # Auth verification
    session_data, status_code = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if status_code != 200:
        return session_data, status_code

    user_uuid = session_data.get("uuid")
    # user_uuid = "4f2e8bb5-38e1-4537-9cfa-11425c3b4284"
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    valid, inventory_item_id = sanitize_uuid_input(inventory_item_id)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def get_item_info():
            # Call the mocked internal function
            item_info, internal_status_code = get_item_by_uuid_internal(uuid=inventory_item_id)
            if internal_status_code == 404:
                return None, 404
            elif internal_status_code != 200:
                raise requests.HTTPError(
                    f"Internal service error: {internal_status_code}",
                    response=type("MockResponse", (object,), {"status_code": internal_status_code})(),
                )

            if not isinstance(item_info, dict):
                raise Exception(f"Invalid response from internal service: {item_info}")

            return item_info, 200

        item_info, status_code = get_item_info()

        if item_info is None:
            return jsonify({"error": "Item not found"}), 404

        # Check if the item belongs to the requesting user
        if item_info["owner_id"] != user_uuid:
            return jsonify({"error": "Not authorized to access this item"}), 403

        return jsonify(item_info), 200

    except requests.HTTPError as e:
        return jsonify({"error": e.args[0]}), e.response.status_code  # Use specific message from error
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def remove_inventory_item():
    """Remove an item from user's inventory."""
    # Auth verification
    session_data, status_code = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if status_code != 200:
        return session_data, status_code

    user_uuid = session_data.get("uuid")

    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    item_uuid = connexion.request.args.get("inventory_item_id")
    if not item_uuid:
        return jsonify({"error": "Missing item_uuid parameter"}), 400

    valid, item_uuid = sanitize_uuid_input(item_uuid)
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:
        # First check if item is in auction (mocked)
        @circuit_breaker
        def check_auction_status():  #### SIMULATED AUCTION CHECK USING MOCK DATA
            # using MOCK_AUCTION_DATA
            session_data, status_code = verify_login(
                connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE
            )
            if status_code != 200:
                return session_data, status_code
            user_uuid = session_data.get("uuid")
            if not user_uuid:
                return jsonify({"error": "Not logged in"}), 403

            for auction_id, auction_data in MOCK_AUCTION_DATA.items():
                if auction_data["inventory_item_id"] == item_uuid:
                    return {"found": auction_data["status"] != "closed"}, 200

            return {"found": False}, 200  # Item not in any auction

        auction_check, auction_status_code = check_auction_status()
        if auction_status_code != 200:
            raise requests.HTTPError(
                f"Auction service error: {auction_status_code}",
                response=type("MockResponse", (object,), {"status_code": auction_status_code})(),
            )

        if auction_check["found"]:
            return jsonify({"error": "Cannot remove item that is currently in auction"}), 400

        # Call the mocked internal function
        response = remove_item_internal(None, item_uuid, user_uuid)
        if response[1] == 404:
            return jsonify({"error": "Item not found."}), 404
        elif response[1] != 200:
            return jsonify({"error": "Service unavailable. Please try again later."}), 503

        return jsonify({"message": "Item removed from inventory."}), 200

    except requests.HTTPError as e:
        return jsonify({"error": e.args[0]}), e.response.status_code
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500
