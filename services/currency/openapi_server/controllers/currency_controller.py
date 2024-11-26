import requests
from flask import jsonify, session
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.logging import send_log

circuit_breaker = CircuitBreaker(
    fail_max=3, reset_timeout=5, exclude=[requests.HTTPError]
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


def health_check():
    return jsonify({"message": "Service operational."}), 200


def buy_currency(bundle_id):
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    # /db_manager/currency/get_bundle_info
    # Returns information about a bundle given its codename.
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "bundle_id": bundle_id
            }
            url = "http://db_manager:8080/db_manager/currency/get_bundle_info"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        bundle = make_request_to_dbmanager()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Bundle not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503

    codename = bundle["codename"]
    currency_name = bundle["currency_name"]
    public_name = bundle["public_name"]
    credits_obtained = bundle["credits_obtained"]
    price = bundle["price"]

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

    
    # /db_manager/currency/purchase_bundle
    # Processes the purchase of a bundle by updating user credits and logging transactions in appropriate tables.
    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "user_uuid": session["uuid"],
                "bundle_codename": codename,
                "currency_name": currency_name,
                "credits_obtained": credits_obtained,
                "transaction_type_bundle_code": TRANSACTION_TYPE_BUNDLE_CODE
            }
            url = "http://db_manager:8080/db_manager/currency/purchase_bundle"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return

        make_request_to_dbmanager()
        return jsonify({"message": "Bundle " + public_name + " successfully bought."}), 200
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Bundle not found."}), 404
        else:  # other errors
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


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