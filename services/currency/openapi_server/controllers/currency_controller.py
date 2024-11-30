import requests
import connexion

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server import util

from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.logging import send_log

from openapi_server.helpers.authorization import verify_login

from openapi_server.controllers.currency_internal_controller import get_bundle

circuit_breaker = CircuitBreaker(
    fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError]
)

TRANSACTION_TYPE_BUNDLE_CODE = "bought_bundle"
global_mock_accounts = {
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": {
        "username": "user1",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 100
            },
            {
                "currency": "USD",
                "amount": 300
            }
        ]
    },
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284": {
        "username": "user1",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 10000
            },
            {
                "currency": "PLN",
                "amount": 300
            }
        ]
    },
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": {
        "username": "user2",
        "accounts": [
            {
                "currency": "USD",
                "amount": 50
            }
        ]
    },
    "16ca8be1-8497-4957-ad5c-ad0bbe2a2863": {
        "username": "user3",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 200
            }
        ]
    }
}


def currency_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def buy_currency(bundle_id):
    session = verify_login(connexion.request.headers.get('Authorization'))
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    response = get_bundle(None, bundle_id)
    if response[1] != 200:
        return response
    
    response_data = response[0].get_json()

    codename = response_data["codename"]
    currency_name = response_data["currency"]
    public_name = response_data["public_name"]
    credits_obtained = response_data["amount"]
    price = response_data["value"]

    candidate_user_account_no = -1
    user_accounts = global_mock_accounts.get(session['uuid'])

    if user_accounts:  # Ensure the user exists
        accounts_list = user_accounts.get("accounts")  # Access the 'accounts' list
        for index, element in enumerate(accounts_list):
            if element["currency"] == currency_name:
                candidate_user_account_no = index

    if user_accounts["accounts"][candidate_user_account_no]["currency"] != currency_name:
        return jsonify({"error": "Different currency needed, contact your bank."}), 400
    
    if user_accounts["accounts"][candidate_user_account_no]["amount"] < price:
        return jsonify({"error": "You cannot afford this bundle."}), 412
    
    user_accounts["accounts"][candidate_user_account_no]["amount"] -= price
    
    try:
        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": session['uuid'],"amount":credits_obtained}
            url = "http://service_profile:8080/profile/internal/add_currency"
            response = requests.post(url, params=params)
            response.raise_for_status()
            return response.json()
        
        make_request_to_profile_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "Item not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

    return jsonify({"message":"Purchase successful."}), 200


def get_bundles():
    # /db_manager/currency/list_bundles
    # Returns a list of all available bundles with their details.
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/currency/list_bundles"
            response = requests.post(url)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        bundles = make_request_to_dbmanager()
        
        if not bundles:
            return jsonify({"error": "No bundles found."}), 404

        # Format the bundles data to match the API response structure
        bundles_list = []
        for bundle in bundles:
            codename, currency_name, public_name, credits_obtained, price = bundle
            bundles_list.append({
                "id": codename,
                "name": public_name,
                "amount": credits_obtained,
                "prices": [
                    {"name": currency_name, "value": price}
                ]
            })
        
        return bundles_list, 200
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No bundles found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503