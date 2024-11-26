import connexion
import requests
import uuid
import random
import logging
import json

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util
from openapi_server.models.rarity_probability import RarityProbability  # noqa: E501
from openapi_server.helpers.logging import send_log
from flask import jsonify, request, session, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import uuid
from datetime import datetime, timedelta
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200



def get_gacha_info(gacha_uuid):  # noqa: E501
    try:
        def make_request_to_dbmanager():
            payload = {
                "gacha_uuid": gacha_uuid
            }
            url = "http://db_manager:8080/db_manager/gachas/get_gacha_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        gacha_data = make_request_to_dbmanager()

        return jsonify(gacha_data), 200
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Gacha not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    
def pull_gacha(pool_id):
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = pool_id
            url = "http://db_manager:8080/db_manager/gachas/get_pool_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        pool = make_request_to_dbmanager()

        probabilities = json.loads(pool["probabilities"])
        price = pool["price"]
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": session['uuid']
            }
            url = "http://db_manager:8080/db_manager/gachas/get_currency"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        currency = make_request_to_dbmanager()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    

    if currency["currency"] < price:
        return jsonify({"error": "Not enough credits"}), 401

    item_list = pool["items"]
    if item_list == []:
        return jsonify({"error": "This pool has no gachas"}), 404

    pullable_gachas = []
    while(pullable_gachas == []):
        rarity_roll = random.random()
        selected_rarity = None
        cumulative_prob = 0
        
        for rarity, prob in probabilities.items():
            cumulative_prob += prob
            if rarity_roll <= cumulative_prob:
                selected_rarity = rarity.upper()
                break
        selected_rarity = selected_rarity.replace("PROBABILITY", "")
        for item in item_list:
            if item["rarity"] == selected_rarity:
                pullable_gachas.append(item)
        if pullable_gachas != []:
            selected_item = random.choice(pullable_gachas)

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "item_uuid": str(uuid.uuid4()),
                "owner_uuid": session['uuid'],
                "stand_uuid": selected_item['gacha_uuid'],
                "price_paid": price
            }
            url = "http://db_manager:8080/db_manager/gachas/give_item"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return 
        
        make_request_to_dbmanager()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    gacha = Gacha(
        gacha_uuid=selected_item['gacha_uuid'],
        name=selected_item['name'],
        rarity=selected_rarity.lower(),
        attributes= selected_item['attributes']
    )

    return jsonify(gacha), 200

def get_pool_info(): 
    
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/gachas/get_pools"
            response = requests.post(url)
            response.raise_for_status()
            return response.json()
        
        pool = make_request_to_dbmanager()
        
        return jsonify(pool), 200
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

def get_gachas(not_owned):  # noqa: E501
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    user_uuid = session['uuid']

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": user_uuid,
                "owned_filter": not_owned  
            }
            url = "http://db_manager:8080/db_manager/gachas/get_gacha_list"
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        
        gacha_list = make_request_to_dbmanager()

        return jsonify(gacha_list), 200
    
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Pool not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503