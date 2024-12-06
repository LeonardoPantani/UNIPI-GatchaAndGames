import requests
import connexion

from openapi_server.models.bundle import Bundle
from openapi_server import util

from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.logging import send_log

from openapi_server.helpers.authorization import verify_login

from openapi_server.helpers.input_checks import sanitize_string_input

from openapi_server.controllers.currency_internal_controller import get_bundle, insert_bundle_transaction, insert_ingame_transaction, list_bundles

circuit_breaker = CircuitBreaker(
    fail_max=5, reset_timeout=5, exclude=[requests.HTTPError]
)

SERVICE_TYPE="currency"
TRANSACTION_TYPE_BUNDLE_CODE = "bought_bundle"
global_mock_accounts= {
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284":{
        "username": "SpeedwagonAdmin",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 100
            }
        ]
    }
}


def currency_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def buy_currency(bundle_id):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    bundle_id = sanitize_string_input(bundle_id)

    if bundle_id == "add_myself_some_currency":
        if session['uuid'] not in global_mock_accounts:
            send_log(f"add_myself_some_currency: User {session['username']} not found in mock account data.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error":"No user account found, try buying a bundle first."}), 404
        else:
            for account in global_mock_accounts[session['uuid']]["accounts"]:
                account['amount'] += 100000
        
        send_log(f"add_myself_some_currency: User {session['username']} has successfully added currency to his balance.", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message":"Balance added"}), 200        

    response = get_bundle(None, bundle_id)
    if response[1] == 404:
        send_log(f"get_bundle: No bundle found with codename {bundle_id} by user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return response
    elif response[1] == 503 or response[1] == 400:
        send_log(f"get_bundle: HttpError {response} for user {session['username']}.", level="error", service_type=SERVICE_TYPE)
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
        send_log(f"buy_currency: Wrong currency for user {session['username']} to buy {bundle_id}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Different currency needed, contact your bank."}), 406
    
    if user_accounts["accounts"][candidate_user_account_no]["amount"] < price:
        send_log(f"buy_currency: Not enough money for user {session['username']} to buy {bundle_id}.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "You cannot afford this bundle."}), 412
    
    user_accounts["accounts"][candidate_user_account_no]["amount"] -= price
    
    response = insert_bundle_transaction(None, session['uuid'], codename, currency_name)
    if response[1] != 200:
        send_log(f"insert_bundle_transaction: HttpError {response} for user {session['username']} with bundle {codename}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    response = insert_ingame_transaction(None, session['uuid'], credits_obtained, TRANSACTION_TYPE_BUNDLE_CODE)
    if response[1] != 200:
        send_log(f"insert_ingame_transaction: HttpError {response} for user {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    try:
        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": session['uuid'], "amount":credits_obtained}
            url = "https://service_profile/profile/internal/add_currency"
            response = requests.post(url, params=params, verify=False)
            response.raise_for_status()
            return response.json()
        
        make_request_to_profile_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            send_log(f"make_request_to_profile_service: No user found with uuid {session['uuid']}.", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        else:
            send_log(f"make_request_to_profile_service: HttpError {e} for user {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        send_log(f"make_request_to_profile_service: RequestException {e} for user {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_profile_service: Circuit breaker is open for user {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

    send_log(f"buy_currency: User {session['username']} has successfully bought bundle {bundle_id}.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message":"Purchase of "+public_name+" successful."}), 200

@circuit_breaker
def get_bundles():
    response = list_bundles(None)
    
    if response[1] != 200:
        send_log(f"list_bundles: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    send_log(f"get_bundles: User {session['username']} has successfully gotten bundles info.", level="general", service_type=SERVICE_TYPE)
    return response