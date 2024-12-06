############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import uuid
from datetime import datetime, timedelta

import connexion
import requests
from flask import jsonify, request
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.controllers.auction_internal_controller import (
    MOCK_INVENTORIES,
    MOCK_PROFILES,
    get_auction,
    get_user_auctions,
    is_open_by_item_uuid,
    set_bid,
)
from openapi_server.controllers.auction_internal_controller import (
    create_auction as create,
)
from openapi_server.controllers.auction_internal_controller import (
    get_auction_list as list_auctions,
)
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_pagenumber_input, sanitize_uuid_input

MOCK_INGAMETRANSACTIONS = {
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "2024-01-05 10:00:00"): (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        1000,
        "bought_bundle",
        "2024-01-05 10:00:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "2024-01-06 11:30:00"): (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        5000,
        "bought_bundle",
        "2024-01-06 11:30:00",
    ),
    ("a4f0c592-12af-4bde-aacd-94cd0f27c57e", "2024-01-07 15:45:00"): (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        3000,
        "bought_bundle",
        "2024-01-07 15:45:00",
    ),
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "2024-01-08 09:15:00"): (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        -1000,
        "gacha_pull",
        "2024-01-08 09:15:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "2024-01-09 14:20:00"): (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        -1200,
        "gacha_pull",
        "2024-01-09 14:20:00",
    ),
}


# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])

SERVICE_TYPE = "auction"
TRANSACTION_TYPE_BUY = "bought_market"
TRANSACTION_TYPE_SELL = "sold_market"


def auction_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def bid_on_auction(auction_uuid):
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione
    _, session["uuid"] = sanitize_uuid_input(session["uuid"])

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
    owner_uuid = response_data["inventory_item_owner_id"]

    if not current_bid:
        new_bid = starting_price
    else:
        new_bid = current_bid + increment

    if session["uuid"] == owner_uuid:
        return jsonify({"error": "Cannot bid on your own auctions"}), 400

    if session["uuid"] == current_bidder:
        return jsonify({"message": "Already the highest bidder"}), 200

    if status == "closed":
        return jsonify({"error": "Auction is closed"}), 403
    try:

        @circuit_breaker
        def make_request_to_profile_service():
            global MOCK_PROFILES

            return MOCK_PROFILES.get(session["uuid"])

        user_profile = make_request_to_profile_service()
        if not user_profile:
            return jsonify({"error": "User not found."}), 404
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    user_currency = user_profile[1]

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
            global MOCK_PROFILES

            if session["uuid"] not in MOCK_PROFILES:
                return 404

            MOCK_PROFILES[session["uuid"]] = (
                MOCK_PROFILES[session["uuid"]][0],
                MOCK_PROFILES[session["uuid"]][1] + (new_bid * -1),
                MOCK_PROFILES[session["uuid"]][2],
                MOCK_PROFILES[session["uuid"]][3],
            )
            return 200

        make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
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
                global MOCK_PROFILES

                if previous_bidder not in MOCK_PROFILES:
                    return 404

                MOCK_PROFILES[previous_bidder] = (
                    MOCK_PROFILES[previous_bidder][0],
                    MOCK_PROFILES[previous_bidder][1] + previous_bid,
                    MOCK_PROFILES[previous_bidder][2],
                    MOCK_PROFILES[previous_bidder][3],
                )
                return 200

            make_request_to_profile_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return jsonify({"message": "Successfully bid " + str(new_bid) + " on auction " + auction_uuid + "."}), 200


def create_auction():
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione
    _, session["uuid"] = sanitize_uuid_input(session["uuid"])

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
            global MOCK_INVENTORIES

            return MOCK_INVENTORIES.get(item_id)

        item = make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if item[0] != session["uuid"]:
        return jsonify({"error": "This item is not yours."}), 401

    auction_id = str(uuid.uuid4())
    end_time = datetime.now() + timedelta(minutes=10)
    response = is_open_by_item_uuid(None, item_id)

    if response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    if response_data["found"] == True:  # noqa: E712
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
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]

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
    current_bidder = response_data["current_bidder"]
    current_bid = response_data["current_bid"]
    item_uuid = response_data["inventory_item_id"]
    owner_uuid = response_data["inventory_item_owner_id"]

    if status == "closed" and current_bidder == session["uuid"] and owner_uuid != session["uuid"]:
        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                global MOCK_INVENTORIES

                return MOCK_INVENTORIES.get(item_uuid)

            item = make_request_to_inventory_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        old_owner_uuid = item[0]

        try:

            @circuit_breaker
            def make_request_to_profile_service():
                global MOCK_PROFILES

                if old_owner_uuid not in MOCK_PROFILES:
                    return 404

                MOCK_PROFILES[old_owner_uuid] = (
                    MOCK_PROFILES[old_owner_uuid][0],
                    MOCK_PROFILES[old_owner_uuid][1] + current_bid,
                    MOCK_PROFILES[old_owner_uuid][2],
                    MOCK_PROFILES[old_owner_uuid][3],
                )
                return 200

            make_request_to_profile_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "User not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_currency_service():
                global MOCK_INGAMETRANSACTIONS

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                MOCK_INGAMETRANSACTIONS[(old_owner_uuid, timestamp)] = (
                    old_owner_uuid,
                    current_bid,
                    TRANSACTION_TYPE_SELL,
                    timestamp,
                )

            make_request_to_currency_service()

        except requests.HTTPError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                global MOCK_INVENTORIES

                if item_uuid not in MOCK_INVENTORIES:
                    return 404

                MOCK_INVENTORIES[item_uuid]["owner_uuid"] = session["uuid"]
                MOCK_INVENTORIES[item_uuid]["currency_spent"] = current_bid
                MOCK_INVENTORIES[item_uuid]["owners_no"] += 1
                return 200

            status_code = make_request_to_inventory_service()
            if status_code != 200:
                return jsonify({"error": "Item not found."})

        except requests.HTTPError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:

            @circuit_breaker
            def make_request_to_currency_service():
                global MOCK_INGAMETRANSACTIONS

                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                MOCK_INGAMETRANSACTIONS[(session["uuid"], timestamp)] = (
                    session["uuid"],
                    current_bid,
                    TRANSACTION_TYPE_BUY,
                    timestamp,
                )

            make_request_to_currency_service()

        except requests.HTTPError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    return response_data, 200


def get_auctions_history(page_number=None):
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]

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
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:  # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else:  # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]

    status = request.args.get("status", "open")
    rarity = request.args.get("rarity")
    page_number = int(request.args.get("page_number", 1))

    page_number = sanitize_pagenumber_input(page_number)

    response = list_auctions(None, status, rarity, page_number)

    if response[1] != 200:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    response_data = response[0].get_json()

    return response_data
