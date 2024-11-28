import connexion
import requests
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.auction_status import AuctionStatus  # noqa: E501
from openapi_server.models.exists_auctions200_response import ExistsAuctions200Response  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.is_open_by_item_uuid200_response import IsOpenByItemUuid200Response  # noqa: E501
from openapi_server import util

from openapi_server.helpers.logging import send_log
from flask import jsonify, request, session, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import uuid
from datetime import datetime, timedelta
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=5, exclude=[requests.HTTPError])

def auction_health_check_get():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def bid_on_auction(auction_uuid): 
    #check if user is logged in
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    user_uuid = session['uuid']
    #get args
    increment = request.args.get('bid', type=int)
    
    if increment < 1:
        return jsonify({"error": "Invalid bid value."}), 400

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "uuid": auction_uuid
            }
            url = "http://db_manager:8080/db_manager/auctions/get_auction_status"
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        
        auction = make_request_to_dbmanager()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Auction not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    item_uuid = auction["inventory_item_id"]
    starting_price = auction["starting_price"]
    current_bid = auction["current_bid"]
    current_bidder = auction["current_bidder"]
    end_time = auction["end_time"]
    owner_uuid = auction["inventory_item_owner_id"]
    status = auction["status"]

    #prepare new data to insert
    if not current_bid:
        new_bid = starting_price
    else:    
        new_bid = current_bid + increment

    if user_uuid == owner_uuid:
            return jsonify({"error":"Cannot bid on your own auctions"}), 400

    if user_uuid == current_bidder:
        return jsonify({"message":"Already the highest bidder"}), 200

    if status == "closed":
        return jsonify({"error":"Auction is closed"}), 403

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid
            }
            url = "http://db_manager:8080/db_manager/auctions/get_currency"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        currency_json = make_request_to_dbmanager()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    #check if user has enough funds
    user_currency = currency_json["currency"]
    if user_currency < new_bid:
        return jsonify({"error": "Insufficient funds."}), 406
    
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "auction_uuid": auction_uuid,
                "new_bid": new_bid
            }
            url = "http://db_manager:8080/db_manager/auctions/place_bid"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return
        
        make_request_to_dbmanager()
        return jsonify({"message": "Successfully bid "+ str(new_bid) +" on auction " + auction_uuid + "."}), 200
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Auction or user not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def create_auction(): 

    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403 

    starting_price = request.args.get('starting_price', default=10, type=int)

    if starting_price < 1:
        return jsonify({"error": "Invalid query parameters."}), 400

    owner_id = request.args.get('inventory_item_owner_id')
    item_id = request.args.get('inventory_item_id')

    if not owner_id or not item_id:
        return jsonify({"error": "Invalid query parameters."}), 400

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": owner_id,
                "item_uuid": item_id
            }
            url = "http://db_manager:8080/db_manager/auctions/get_item_with_owner"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        item = make_request_to_dbmanager()
        if item['owner_id'] != session['uuid']:
            return jsonify({"error": "This item is not yours."}), 401
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Item not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    auction_id = str(uuid.uuid4())
    end_time = datetime.now() + timedelta(minutes=10)
    
    try:
        @circuit_breaker
        def make_request_to_db_manager():
            payload = {
                "auction":{
                    "auction_uuid": auction_id,
                    "status": "open",
                    "inventory_item_owner_id": owner_id,
                    "inventory_item_id": item_id,
                    "starting_price": starting_price,
                    "current_bid": 0,
                    "current_bidder": "",
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            url = "http://db_manager:8080/db_manager/auctions/create"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_db_manager()

        return jsonify({"message":"Auction created successfully."}), 201
    
    except requests.HTTPError as e:
        if e.response.status_code == 409:
            return jsonify({"error": "Another auction on the same item is still active."}), 409
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_auction_status(auction_uuid): 
    
    if 'username' not in session:
        return jsonify({"error":"Not logged in"}), 403
    
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "uuid": auction_uuid
            }
            url = "http://db_manager:8080/db_manager/auctions/get_auction_status"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        auction = make_request_to_dbmanager()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Auction not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    if auction["status"] == 'closed':
        try:
            
            @circuit_breaker
            def make_request_to_dbmanager():
                payload = {
                    "item_uuid": auction['inventory_item_id'],
                    "current_bid": auction['current_bid'],
                    "user_uuid": auction['current_bidder']
                }
                url = "http://db_manager:8080/db_manager/auctions/complete_sale"
                response = requests.post(url, json=payload)
                response.raise_for_status()  # if response is obtained correctly
                return 

            make_request_to_dbmanager()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "Item or user not found."}), 404
            else:  # other errors
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
            return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    return auction, 200

def get_auctions_history(page_number=None):  
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403
    
    user_uuid=session['uuid']
    page_number = int(request.args.get('page_number', 1))
    
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "page_number": page_number
            }
            url = "http://db_manager:8080/db_manager/auctions/get_user_involved_auctions"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        auction_list = make_request_to_dbmanager()

        return jsonify(auction_list), 200
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No auctions found for user "+ user_uuid}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_auctions_list(status=None, rarity=None, page_number=None): 
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    status = request.args.get('status','open')
    rarity = request.args.get('rarity')
    page_number = int(request.args.get('page_number',1))

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "status": status,
                "page_number": page_number
            }
            if rarity is not None:
                payload["rarity"] = rarity
            
            url = "http://db_manager:8080/db_manager/auctions/list"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        auction_list = make_request_to_dbmanager()

        return jsonify(auction_list), 200
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No auctions found"}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503        
