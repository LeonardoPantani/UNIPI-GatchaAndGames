import requests
import connexion

from openapi_server.models.bundle import Bundle
from openapi_server import util

from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.logging import send_log

from openapi_server.helpers.authorization import verify_login

from openapi_server.controllers.currency_internal_controller import get_bundle, insert_bundle_transaction, insert_ingame_transaction, list_bundles

circuit_breaker = CircuitBreaker(
    fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError]
)

TRANSACTION_TYPE_BUNDLE_CODE = "bought_bundle"
global_mock_accounts = {

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
    if response[1] == 404:
        return response
    elif response[1] == 503 or response[1] == 400:
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    
    response_data = response[0].get_json()

    codename = response_data["codename"]
    currency_name = response_data["currency"]
    public_name = response_data["public_name"]
    credits_obtained = response_data["amount"]
    price = response_data["value"]

    candidate_user_account_no = -1
    user_accounts = global_mock_accounts.get(session['uuid'])

    if not user_accounts: #simplification of contacting a bank, we generate an account binded to the user if it's not present in global mock data
        global_mock_accounts[session['uuid']] = {
            "username": session['username'],
            "accounts": [
                {
                    "currency": currency_name,
                    "amount": (3 * price) + 1
                }
            ]
        }
        user_accounts = global_mock_accounts[session['uuid']]

    accounts_list = user_accounts.get("accounts")  # Access the 'accounts' list
    for index, element in enumerate(accounts_list):
        if element["currency"] == currency_name:
            candidate_user_account_no = index

    if user_accounts["accounts"][candidate_user_account_no]["currency"] != currency_name:
        return jsonify({"error": "Different currency needed, contact your bank."}), 400
    
    if user_accounts["accounts"][candidate_user_account_no]["amount"] < price:
        return jsonify({"error": "You cannot afford this bundle."}), 412
    
    user_accounts["accounts"][candidate_user_account_no]["amount"] -= price
    
    response = insert_bundle_transaction(None, session['uuid'], codename, currency_name)
    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    response = insert_ingame_transaction(None, session['uuid'], credits_obtained, TRANSACTION_TYPE_BUNDLE_CODE)
    if response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    try:
        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": session['uuid'], "amount":credits_obtained}
            url = "https://service_profile/profile/internal/add_currency"
            response = requests.post(url, params=params)
            response.raise_for_status()
            return response.json()
        
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

    return jsonify({"message":"Purchase of "+public_name+" successful."}), 200

@circuit_breaker
def get_bundles():
    response = list_bundles(None)
    
    if response[1] != 200:
        jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    return response