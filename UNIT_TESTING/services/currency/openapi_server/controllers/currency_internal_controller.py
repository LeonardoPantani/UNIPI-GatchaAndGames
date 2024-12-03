############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import datetime
import string
from flask import jsonify
from mysql.connector.errors import (
    DatabaseError,
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log

MOCK_BUNDLES = {
    "bundle_arrowEUR": ("bundle_arrowEUR", "EUR", "Stand Arrow Bundle", 1000, 9.99),
    "bundle_requiemEUR": ("bundle_requiemEUR", "EUR", "Requiem Arrow Bundle", 3000, 24.99),
    "bundle_heavenEUR": ("bundle_heavenEUR", "EUR", "Heaven's Bundle", 5000, 49.99),
    "bundle_arrowUSD": ("bundle_arrowUSD", "USD", "Stand Arrow Bundle", 1000, 10.99),
    "bundle_requiemUSD": ("bundle_requiemUSD", "USD", "Requiem Arrow Bundle", 3000, 27.99),
    "bundle_heavenUSD": ("bundle_heavenUSD", "USD", "Heaven's Bundle", 5000, 54.99),
}

MOCK_BUNDLESTRANSACTIONS = {
    ("e3b0c44298fc1c14b39f92d1282048c0", "bundle_arrowEUR", "2024-01-05 10:00:00"): ("bundle_arrowEUR", "EUR", "e3b0c44298fc1c14b39f92d1282048c0", "2024-01-05 10:00:00"),
    ("87f3b5d15e8e4fa4909b3cd29f4b1f09", "bundle_heavenUSD", "2024-01-06 11:30:00"): ("bundle_heavenUSD", "USD", "87f3b5d15e8e4fa4909b3cd29f4b1f09", "2024-01-06 11:30:00"),
    ("a4f0c59212af4bdeaacd94cd0f27c57e", "bundle_requiemEUR", "2024-01-07 15:45:00"): ("bundle_requiemEUR", "EUR", "a4f0c59212af4bdeaacd94cd0f27c57e", "2024-01-07 15:45:00"),
}

MOCK_INGAMETRANSACTIONS = {
    ("e3b0c44298fc1c14b39f92d1282048c0", "2024-01-05 10:00:00"): ("e3b0c44298fc1c14b39f92d1282048c0", 1000, "bought_bundle", "2024-01-05 10:00:00"),
    ("87f3b5d15e8e4fa4909b3cd29f4b1f09", "2024-01-06 11:30:00"): ("87f3b5d15e8e4fa4909b3cd29f4b1f09", 5000, "bought_bundle", "2024-01-06 11:30:00"),
    ("a4f0c59212af4bdeaacd94cd0f27c57e", "2024-01-07 15:45:00"): ("a4f0c59212af4bdeaacd94cd0f27c57e", 3000, "bought_bundle", "2024-01-07 15:45:00"),
    ("e3b0c44298fc1c14b39f92d1282048c0", "2024-01-08 09:15:00"): ("e3b0c44298fc1c14b39f92d1282048c0", -1000, "gacha_pull", "2024-01-08 09:15:00"),
    ('87f3b5d15e8e4fa4909b3cd29f4b1f09', '2024-01-09 14:20:00'): ('87f3b5d15e8e4fa4909b3cd29f4b1f09', -1200, "gacha_pull", '2024-01-09 14:20:00')
}

SERVICE_TYPE="currency"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def delete_user_transactions(session=None, uuid=None):
    if not uuid:
        return "", 400
    uuid = ''.join(char for char in uuid if char not in string.punctuation)

    try:
        @circuit_breaker
        def delete_transactions():
            global MOCK_BUNDLESTRANSACTIONS, MOCK_INGAMETRANSACTIONS

            MOCK_BUNDLESTRANSACTIONS = {
                k: v for k, v in MOCK_BUNDLESTRANSACTIONS.items() if k[0] != uuid
            }
            MOCK_INGAMETRANSACTIONS = {
                k: v for k, v in MOCK_INGAMETRANSACTIONS.items() if k[0] != uuid
            }

        delete_transactions()
        return jsonify({"message": "Transactions deleted."}), 200

    except CircuitBreakerError:
        return "", 503


def get_bundle(session=None, codename=None):
    if not codename:
        return "", 400

    try:
        @circuit_breaker
        def get_bundle_info():
            # Recuperare il bundle da MOCK_BUNDLES
            return MOCK_BUNDLES.get(codename)

        bundle_info = get_bundle_info()

        if not bundle_info:
            return "", 404

        payload = {
            "codename": bundle_info[0],
            "public_name": bundle_info[2],
            "amount": bundle_info[3],
            "currency": bundle_info[1],
            "value": bundle_info[4]
        }

        return jsonify(payload), 200

    except CircuitBreakerError:
        return "", 503


def get_user_history(session=None, uuid=None, history_type=None, page_number=None):
    if not uuid or not history_type:
        return "", 400
    uuid = ''.join(char for char in uuid if char not in string.punctuation)

    if history_type not in ["bundle", "ingame"]:
        return "", 400

    items_per_page = 10
    offset = (page_number - 1) * items_per_page

    try:
        @circuit_breaker
        def get_user_transactions():
            if history_type == "bundle":
                transactions = [
                    v for k, v in MOCK_BUNDLESTRANSACTIONS.items() if k[0] == uuid
                ]
            else:
                transactions = [
                    v for k, v in MOCK_INGAMETRANSACTIONS.items() if k[0] == uuid
                ]
            return transactions[offset:offset + items_per_page]

        transaction_list = get_user_transactions()

        response = []

        for transaction in transaction_list:
            if history_type == "bundle":
                payload = {
                    "user_uuid": transaction[2],
                    "timestamp": transaction[3],
                    "codename": transaction[0],
                    "currency_name": transaction[1]
                }
            else:
                payload = {
                    "user_uuid": transaction[0],
                    "timestamp": transaction[3],
                    "credits": transaction[1],
                    "transaction_type": transaction[2]
                }
            response.append(payload)

        return jsonify(response), 200

    except CircuitBreakerError:
        return "", 503


def insert_bundle_transaction(session=None, uuid=None, bundle_codename=None, currency_name=None):
    if not uuid or not bundle_codename or not currency_name:
        return "", 400
    uuid = ''.join(char for char in uuid if char not in string.punctuation)
    try:
        @circuit_breaker
        def insert_transaction():
            # Inserire una nuova transazione in MOCK_BUNDLESTRANSACTIONS
            global MOCK_BUNDLESTRANSACTIONS

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            MOCK_BUNDLESTRANSACTIONS[(uuid, bundle_codename, timestamp)] = (
                bundle_codename,
                currency_name,
                uuid,
                timestamp
            )

        insert_transaction()
        return jsonify({"message": "Transaction inserted."}), 200

    except CircuitBreakerError:
        return "", 503


def insert_ingame_transaction(session=None, uuid=None, current_bid=None, transaction_type=None):
    if not uuid or not current_bid or not transaction_type:
        return "", 400
    uuid = ''.join(char for char in uuid if char not in string.punctuation)

    if transaction_type not in ["bought_bundle", "sold_market", "bought_market", "gacha_pull"]:
        return "", 400

    try:
        @circuit_breaker
        def insert_transaction():
            # Inserire una nuova transazione in MOCK_INGAMETRANSACTIONS
            global MOCK_INGAMETRANSACTIONS

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            MOCK_INGAMETRANSACTIONS[(uuid, timestamp)] = (
                uuid,
                current_bid,
                transaction_type,
                timestamp
            )

        insert_transaction()
        return jsonify({"message": "Transaction inserted."}), 200

    except CircuitBreakerError:
        return "", 503


def list_bundles(session=None):
    try:
        @circuit_breaker
        def get_bundles():
            # Recuperare tutti i bundle da MOCK_BUNDLES
            return MOCK_BUNDLES.values()

        bundles_list = get_bundles()

    except CircuitBreakerError:
        return "", 503

    response = []

    for bundle in bundles_list:
        payload = {
            "codename": bundle[0],
            "public_name": bundle[2],
            "amount": bundle[3],
            "currency": bundle[1],
            "value": bundle[4]
        }
        response.append(payload)

    return jsonify(response), 200