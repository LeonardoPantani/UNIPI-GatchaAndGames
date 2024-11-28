import connexion
import logging
from openapi_server.models.get_bundle_info_request import GetBundleInfoRequest
from openapi_server.models.purchase_bundle_request import PurchaseBundleRequest
from flask import jsonify
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log


circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])



def get_bundle_info(get_bundle_info_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_bundle_info_request = GetBundleInfoRequest.from_dict(connexion.request.get_json())
    
    # valid json request
    bundle_id = get_bundle_info_request.bundle_id
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            # Get the bundle details from the database
            cursor.execute(
                'SELECT codename, currency_name, public_name, credits_obtained, price FROM bundles WHERE codename = %s',
                (bundle_id,)
            )
            return cursor.fetchone()

        bundle = make_request_to_db()

        if not bundle:
            return "", 404
        
        payload = {
            "codename": bundle[0],
            "currency_name": bundle[1],
            "public_name": bundle[2],
            "credits_obtained": bundle[3],
            "price": int(bundle[4])
        }

        return payload, 200
    except OperationalError:
        logging.error("Query ["+ bundle_id +"]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ bundle_id +"]: Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query ["+ bundle_id +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ bundle_id +"]: Data error.")
        return "", 500
    except InternalError:
        logging.error("Query ["+ bundle_id +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ bundle_id +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ bundle_id +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def list_bundles():
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(""" 
                SELECT codename, currency_name, public_name, credits_obtained, price
                FROM bundles
            """)
            return cursor.fetchall()

        ret = make_request_to_db()

        return ret, 200
    except OperationalError:
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query: Programming error.")
        return "", 400
    except IntegrityError:
        logging.error("Query: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query: Data error.")
        return "", 400
    except InternalError:
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def purchase_bundle(purchase_bundle_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    purchase_bundle_request = PurchaseBundleRequest.from_dict(connexion.request.get_json())
    
    # valid json request
    user_uuid = purchase_bundle_request.user_uuid
    bundle_codename = purchase_bundle_request.bundle_codename
    currency_name = purchase_bundle_request.currency_name
    credits_obtained = purchase_bundle_request.credits_obtained
    transaction_type_bundle_code = purchase_bundle_request.transaction_type_bundle_code
    
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE profiles SET currency = currency + %s WHERE uuid = UUID_TO_BIN(%s)',
                (credits_obtained, user_uuid)
            )
            # aggiungi 404
            cursor.execute(
                'INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES (%s, %s, UUID_TO_BIN(%s))',
                (bundle_codename, currency_name, user_uuid)
            )
            # probabile integrity error, eventualmente restituire 409
            cursor.execute(
                'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, %s)',
                (user_uuid, credits_obtained, transaction_type_bundle_code)
            )
            connection.commit()
            return

        make_request_to_db()

        return "", 200
    except OperationalError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Programming error.")
        return "", 400
    except IntegrityError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Data error.")
        return "", 400
    except InternalError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ user_uuid + ", " + bundle_codename +"]: Database error.")
        return "", 401
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
