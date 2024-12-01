import logging

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

SERVICE_TYPE="currency"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def delete_user_transactions(session=None, uuid=None):
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def delete_transactions():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                DELETE 
                FROM bundles_transactions
                WHERE user_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            query = """
                DELETE 
                FROM ingame_transactions
                WHERE user_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            cursor.close()

            connection.commit()

        delete_transactions()

        return jsonify({"message": "Transactions deleted."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503

def get_bundle(session=None, codename=None):
    if not codename:
        "", 400

    try:
        @circuit_breaker
        def get_bundle_info():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT codename, public_name, credits_obtained, currency_name, price
                FROM bundles
                WHERE codename = %s
            """

            cursor.execute(query, (codename,))

            bundle_data = cursor.fetchall()
            
            cursor.close()

            if not bundle_data:
                return None
   
            return bundle_data[0]
        
        bundle_info = get_bundle_info()

        if not bundle_info:
            return "", 404

        payload = {
            "codename": bundle_info[0],
            "public_name": bundle_info[1],
            "amount": bundle_info[2],
            "currency": bundle_info[3],
            "value": bundle_info[4]
        }

        return jsonify(payload), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503

def get_user_history(session=None, uuid=None, history_type=None, page_number=None):
    if not uuid or not history_type:
        return "", 400
    
    if history_type != "bundle" and history_type!= "ingame":
        return "", 400
    
    items_per_page = 10
    offset = (page_number - 1) * items_per_page

    try:
        @circuit_breaker
        def get_user_transactions():
            connection = get_db()
            cursor = connection.cursor()

            if history_type == "bundle":
                query = """
                    SELECT BIN_TO_UUID(user_uuid), timestamp, bundle_codename, bundle_currency_name
                    FROM bundles_transactions
                    WHERE user_uuid = UUID_TO_BIN(%s)
                    LIMIT %s
                    OFFSET %s
                """
            else:
                query = """
                    SELECT BIN_TO_UUID(user_uuid), timestamp, credits, transaction_type
                    FROM ingame_transactions
                    WHERE user_uuid = UUID_TO_BIN(%s)
                    LIMIT %s
                    OFFSET %s
                """

            cursor.execute(query, (uuid, items_per_page, offset))

            transaction_data = cursor.fetchall()

            cursor.close()

            return transaction_data
        
        transaction_list = get_user_transactions()
        
        response = []

        for transaction in transaction_list:
            if history_type == "bundle":
                payload = {
                    "user_uuid": transaction[0],
                    "timestamp": transaction[1],
                    "codename": transaction[2],
                    "currency_name": transaction[3]
                }
            else:
                payload = {
                    "user_uuid": transaction[0],
                    "timestamp": transaction[1],
                    "credits": transaction[2],
                    "transaction_type": transaction[3]
                }
            response.append(payload)
        
        return jsonify(response), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503    


def insert_bundle_transaction(session=None, uuid=None, bundle_codename=None, currency_name=None):
    if not uuid or not bundle_codename or not currency_name:
        return "", 400
    
    try:
        @circuit_breaker
        def insert_transaction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                INSERT INTO bundles_transactions
                (bundle_codename, bundle_currency_name, user_uuid)
                VALUES (%s, %s, UUID_TO_BIN(%s))
            """

            cursor.execute(query, (bundle_codename, currency_name, uuid))

            cursor.close()

            connection.commit()

        insert_transaction()

        return jsonify({"message": "Transaction inserted."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503    

def insert_ingame_transaction(session=None, uuid=None, current_bid=None, transaction_type=None):
    if not uuid or not current_bid or not transaction_type:
        return "", 400
    
    if transaction_type != "bought_bundle" and transaction_type != "sold_market" and transaction_type != "bought_market" and transaction_type != "gacha_pull":
        return "", 400

    try:
        @circuit_breaker
        def insert_transaction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                INSERT INTO ingame_transactions
                (user_uuid, credits, transaction_type)
                VALUES (UUID_TO_BIN(%s), %s, %s)
            """

            cursor.execute(query, (uuid, current_bid, transaction_type))

            cursor.close()

            connection.commit()

        insert_transaction()

        return jsonify({"message": "Transaction inserted."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503    


def list_bundles(session=None):
    
    try:
        @circuit_breaker
        def get_bundles():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT codename, public_name, credits_obtained, currency_name, price
                FROM bundles
            """

            cursor.execute(query)

            bundles_data = cursor.fetchall()

            cursor.close()

            return bundles_data
        
        bundles_list = get_bundles()

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503    
    
    response = []

    for bundle in bundles_list:
        payload = {
            "codename": bundle[0],
            "public_name": bundle[1],
            "amount": bundle[2],
            "currency": bundle[3],
            "value": bundle[4]
        }
        response.append(payload)

    return jsonify(response), 200