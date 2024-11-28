import traceback
import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import session, jsonify
from openapi_server.helpers.logging import send_log
import logging
import requests

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance for inventory operations
circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=5, exclude=[requests.HTTPError])

def inventory_health_check_get():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def get_inventory():  # noqa: E501
    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403
    
    page_number = connexion.request.args.get('page_number', default=1, type=int)
    
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "page_number": page_number
            }
            url = "http://db_manager:8080/db_manager/inventory/get_user_inventory_items"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        inventory_items = make_request_to_dbmanager()

        return jsonify(inventory_items), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No item found"}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503  

def get_inventory_item_info(inventory_item_id):  # noqa: E501
    user_uuid = session.get('uuid')
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "inventory_item_id": inventory_item_id
            }
            url = "http://db_manager:8080/db_manager/inventory/get_user_item_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        item = make_request_to_dbmanager()

        return jsonify(item), 200

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No item found"}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503  


def remove_inventory_item():
     # Get item_id from request args
    item_id = connexion.request.args.get('inventory_item_id')
    if not item_id:
        return jsonify({"error": "Missing inventory_item_id parameter"}), 400
    
    user_uuid = session.get('uuid')
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "inventory_item_id": item_id
            }
            url = "http://db_manager:8080/db_manager/inventory/remove_user_item"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return 
        
        make_request_to_dbmanager()

        return jsonify({"message": "Item successfully removed."}), 200
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No item found"}), 404
        elif e.response.status_code == 409:
            return jsonify({"error": "Cannot remove item that is in an active auction."}), 409
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503 