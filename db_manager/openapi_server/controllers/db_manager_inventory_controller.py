import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.get_inventory_item_request import GetInventoryItemRequest
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest
from openapi_server.models.inventory_item import InventoryItem
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging

# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def get_inventory_item(get_inventory_item_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_inventory_item_request = GetInventoryItemRequest.from_dict(connexion.request.get_json())

    user_uuid = get_inventory_item_request.user_uuid
    item_id = get_inventory_item_request.inventory_item_id

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    BIN_TO_UUID(item_uuid) as item_id,
                    BIN_TO_UUID(owner_uuid) as owner_id,
                    BIN_TO_UUID(stand_uuid) as gacha_uuid,
                    obtained_at,
                    owners_no,
                    currency_spent
                FROM inventories
                WHERE owner_uuid = UUID_TO_BIN(%s) 
                AND item_uuid = UUID_TO_BIN(%s)
        ''', (user_uuid, item_id))
            item_data = cursor.fetchone()
            return item_data
        
        item = make_request_to_db()
        if not item:
            return "", 404
            
        payload = {
            "owner_id": item[1],
            "item_id": item[0],
            "gacha_uuid": item[2],
            "obtained_date": item[3].strftime("%Y-%m-%d %H:%M:%S"),
            "owners_no": item[4],
            "price_paid": item[5]
        }

        return jsonify(payload), 200
    
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ item_id +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ item_id +"]: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ item_id +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ item_id +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ item_id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ item_id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ item_id +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_inventory_items(get_user_involved_auctions_request=None):
    if not connexion.request.is_json:
        return "", 400    
    get_user_inventory_request = GetUserInvolvedAuctionsRequest.from_dict(connexion.request.get_json())

    user_uuid = get_user_inventory_request.user_uuid
    page_number = get_user_inventory_request.page_number

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()

            items_per_page = 10
            offset = (page_number - 1) * items_per_page

            cursor.execute('''
                SELECT 
                    BIN_TO_UUID(item_uuid),
                    BIN_TO_UUID(owner_uuid),
                    BIN_TO_UUID(stand_uuid),
                    obtained_at,
                    owners_no,
                    currency_spent
                FROM inventories
                WHERE owner_uuid = UUID_TO_BIN(%s)
                LIMIT %s OFFSET %s
            ''', (user_uuid, items_per_page, offset))

            return cursor.fetchall()
        
        item_list = make_request_to_db()

        inventory_items = []
        for row in item_list:
            item = {
                "owner_id": row[1],
                "item_id": row[0],
                "gacha_uuid": row[2],
                "obtained_date": row[3].strftime("%Y-%m-%d %H:%M:%S"),
                "owners_no": row[4],
                "price_paid": row[5]
            }
            inventory_items.append(item)
            
        return jsonify(inventory_items), 200

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid +"]: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503       


def remove_item(get_inventory_item_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_inventory_item_request = GetInventoryItemRequest.from_dict(connexion.request.get_json())

    user_uuid = get_inventory_item_request.user_uuid
    item_id = get_inventory_item_request.inventory_item_id

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()

            cursor.execute('''
                SELECT 1 FROM auctions 
                WHERE item_uuid = UUID_TO_BIN(%s)
                AND end_time > NOW()
            ''', (item_id,))

            if cursor.fetchone():
                return 409

            # Delete the item
            cursor.execute('''
                DELETE FROM inventories 
                WHERE item_uuid = UUID_TO_BIN(%s)
                AND owner_uuid = UUID_TO_BIN(%s)
            ''', (item_id, user_uuid))
            
            if cursor.rowcount == 0:
                return 404

            connection.commit()
            return 200
        
        response = make_request_to_db()
        if response == 409:
            return "", 409
        elif response == 404:
            return "", 404
        
        return "", 200
        
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ item_id +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ item_id +"]: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ item_id +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ item_id +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ item_id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ item_id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ item_id +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503