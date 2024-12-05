import uuid
from datetime import datetime, timedelta

import connexion
import requests
from flask import current_app, jsonify, request, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from openapi_server import util
from openapi_server.controllers.auction_internal_controller import (
    create_auction as create,
)
from openapi_server.controllers.auction_internal_controller import (
    get_auction,
    get_user_auctions,
    is_open_by_item_uuid,
    set_bid,
)
from openapi_server.controllers.auction_internal_controller import (
    get_auction_list as list_auctions,
)
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_pagenumber_input, sanitize_uuid_input
from openapi_server.helpers.logging import send_log
from openapi_server.models.auction import Auction
from openapi_server.models.auction_status import AuctionStatus
from openapi_server.models.exists_auctions200_response import ExistsAuctions200Response
from openapi_server.models.gacha_rarity import GachaRarity
from openapi_server.models.is_open_by_item_uuid200_response import IsOpenByItemUuid200Response

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

SERVICE_TYPE = "auction"
TRANSACTION_TYPE_BUY = "bought_market"
TRANSACTION_TYPE_SELL = "sold_market"


def auction_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def bid_on_auction(auction_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK
    increment = request.args.get("bid", type=int)

    if increment < 1:
        return jsonify({"error": "Invalid bid value."}), 400

    valid, auction_uuid = sanitize_uuid_input(auction_uuid)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    response = get_auction(None, auction_uuid)
    if response[1] == 404:
        return response
    elif response[1] == 503 or response[1] == 400:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    status = response_data["status"]
    starting_price = response_data["starting_price"]
    current_bidder = response_data["current_bidder"]
    current_bid = response_data["current_bid"]
    item_uuid = response_data["inventory_item_id"]
    end_time = response_data["end_time"]
    owner_uuid = response_data["inventory_item_owner_id"]

    if not current_bid:
        new_bid = starting_price
    else:
        new_bid = current_bid + increment

    if session["uuid"] == owner_uuid:
        return jsonify({"error": "Cannot bid on your own auctions"}), 403

    if session["uuid"] == current_bidder:
        return jsonify({"message": "Already the highest bidder"}), 200

    if status == "closed":
        return jsonify({"error": "Auction is closed"}), 403
    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"user_uuid": session["uuid"]}
            url = "https://service_profile/profile/internal/get_profile"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        user_profile = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_currency = user_profile["currency"]

    if user_currency < new_bid:
        return jsonify({"error": "Insufficient funds."}), 406

    response = set_bid(None, auction_uuid, session["uuid"], new_bid)
    if response[1] == 404:
        return response
    elif response[1] == 503 or response[1] == 400:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": session["uuid"], "amount": new_bid * (-1)}
            url = "https://service_profile/profile/internal/add_currency"
            response = requests.post(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if current_bidder:
        previous_bid = current_bid
        previous_bidder = current_bidder
        try:

            @circuit_breaker
            def make_request_to_profile_service():
                params = {"uuid": previous_bidder, "amount": previous_bid}
                url = "https://service_profile/profile/internal/add_currency"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            make_request_to_profile_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Successfully bid " + str(new_bid) + " on auction " + auction_uuid + "."}), 200


def create_auction():
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    starting_price = request.args.get("starting_price", default=10, type=int)

    if starting_price < 1:
        return jsonify({"error": "Invalid query parameters."}), 400

    owner_id = request.args.get("inventory_item_owner_id")
    item_id = request.args.get("inventory_item_id")

    if not owner_id or not item_id:
        return jsonify({"error": "Invalid query parameters."}), 400

    valid, owner_id = sanitize_uuid_input(owner_id)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    valid, item_id = sanitize_uuid_input(item_id)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"uuid": item_id}
            url = "https://service_inventory/inventory/internal/get_by_item_uuid"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        item = make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if item["owner_id"] != session["uuid"]:
        return jsonify({"error": "This item is not yours."}), 401

    auction_id = str(uuid.uuid4())
    end_time = datetime.now() + timedelta(minutes=10)

    response = is_open_by_item_uuid(None, item_id)

    if response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    if response_data["found"] == True:
        return jsonify({"error": "Another auction on the same item is still active."}), 409

    auction_data = {
        "auction_uuid": auction_id,
        "status": "open",
        "inventory_item_owner_id": session["uuid"],
        "inventory_item_id": item_id,
        "starting_price": starting_price,
        "current_bid": 0,
        "current_bidder": "",
        "end_time": end_time,
    }

    response = create(auction=auction_data)

    return response


def get_auction_status(auction_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    valid, auction_uuid = sanitize_uuid_input(auction_uuid)
    if not valid:
        return jsonify({"error": "Invalid input."}), 400

    response = get_auction(None, auction_uuid)
    if response[1] == 404:
        return response
    elif response[1] == 503 or response[1] == 400:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    status = response_data["status"]
    starting_price = response_data["starting_price"]
    current_bidder = response_data["current_bidder"]
    current_bid = response_data["current_bid"]
    item_uuid = response_data["inventory_item_id"]
    end_time = response_data["end_time"]
    owner_uuid = response_data["inventory_item_owner_id"]

    if status == "closed" and current_bidder == session["uuid"] and owner_uuid != session["uuid"]:
        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": item_uuid}
                url = "https://service_inventory/inventory/internal/get_by_item_uuid"
                response = requests.get(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            item = make_request_to_inventory_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        old_owner_uuid = item["owner_id"]

        try:

            @circuit_breaker
            def make_request_to_profile_service():
                params = {"uuid": old_owner_uuid, "amount": current_bid}
                url = "https://service_profile/profile/internal/add_currency"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            make_request_to_profile_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_currency_service():
                params = {"uuid": old_owner_uuid, "current_bid": current_bid, "transaction_type": TRANSACTION_TYPE_SELL}
                url = "https://service_currency/currency/internal/insert_ingame_transaction"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            make_request_to_currency_service()

        except requests.HTTPError as e:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"new_owner_uuid": session["uuid"], "item_uuid": item_uuid, "price_paid": current_bid}
                url = "https://service_inventory/inventory/internal/update_item_owner"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            make_request_to_inventory_service()

        except requests.HTTPError as e:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_currency_service():
                params = {"uuid": session["uuid"], "current_bid": current_bid, "transaction_type": TRANSACTION_TYPE_BUY}
                url = "https://service_currency/currency/internal/insert_ingame_transaction"
                response = requests.post(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            make_request_to_currency_service()

        except requests.HTTPError as e:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return response_data, 200


def get_auctions_history(page_number=None):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    user_uuid = session["uuid"]
    page_number = int(request.args.get("page_number", 1))

    page_number = sanitize_pagenumber_input(page_number)

    items_per_page = 10
    offset = (page_number - 1) * items_per_page

    response = get_user_auctions(None, user_uuid)

    if response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    return jsonify(response_data[offset : (offset + items_per_page)]), 200


def get_auctions_list(status=None, rarity=None, page_number=None):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]

    status = request.args.get("status", "open")
    rarity = request.args.get("rarity")
    page_number = int(request.args.get("page_number", 1))

    page_number = sanitize_pagenumber_input(page_number)

    response = list_auctions(None, status, rarity, page_number)

    if response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    return response_data
