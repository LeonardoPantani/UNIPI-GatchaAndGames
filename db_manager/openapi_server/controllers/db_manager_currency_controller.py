import connexion
import logging
from openapi_server.models.get_bundle_info_request import GetBundleInfoRequest
from openapi_server.models.purchase_bundle_request import PurchaseBundleRequest
from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError


# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])



def get_bundle_info(get_bundle_info_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_bundle_info_request = GetBundleInfoRequest.from_dict(connexion.request.get_json())
    
    # valid json request
    bundle_id = get_bundle_info_request.bundle_id
    
    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            # Get the bundle details from the database
            cursor.execute(
                'SELECT codename, currency_name, public_name, credits_obtained, price FROM bundles WHERE codename = %s',
                (bundle_id,)
            )
            return cursor.fetchone()

        bundle = make_request_to_db()

        if not bundle:
            return jsonify({"error": "Bundle not found for the given codename."}), 404
        
        payload = {
            "codename": bundle[0],
            "currency_name": bundle[1],
            "public_name": bundle[2],
            "credits_obtained": bundle[3],
            "price": int(bundle[4])
        }

        return payload, 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ bundle_id +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ bundle_id +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ bundle_id +"]: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ bundle_id +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ bundle_id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ bundle_id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ bundle_id +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def list_bundles():
    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(""" 
                SELECT codename, currency_name, public_name, credits_obtained, price
                FROM bundles
            """)
            return cursor.fetchall()

        ret = make_request_to_db()

        return ret, 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
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
    
    mysql = current_app.extensions.get('mysql')
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE profiles SET currency = currency + %s WHERE uuid = UUID_TO_BIN(%s)',
                (credits_obtained, user_uuid)
            )
            cursor.execute(
                'INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES (%s, %s, UUID_TO_BIN(%s))',
                (bundle_codename, currency_name, user_uuid)
            )
            cursor.execute(
                'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, %s)',
                (user_uuid, credits_obtained, transaction_type_bundle_code)
            )
            connection.commit()
            return

        make_request_to_db() 

        return "", 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ purchase_bundle_request +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ purchase_bundle_request +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ purchase_bundle_request +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ purchase_bundle_request +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ purchase_bundle_request +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ purchase_bundle_request +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ purchase_bundle_request +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
