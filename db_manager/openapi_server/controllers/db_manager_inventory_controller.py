import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.get_inventory_item_request import GetInventoryItemRequest  # noqa: E501
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest  # noqa: E501
from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging

# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def get_inventory_item(get_inventory_item_request=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    get_inventory_item_request = GetInventoryItemRequest.from_dict(connexion.request.get_json())  # noqa: E501

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
            return jsonify({"error": "Item not found in player's inventory."}), 404
        
        payload = {
            "owner_id": item[1],
            "item_id": item[0],
            "gacha_uuid": item[2],
            "pull_date": None, #forse si aggiunge
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
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ item_id +"]: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ item_id +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ item_id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ item_id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ item_id +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_inventory_items(get_user_involved_auctions_request=None):  # noqa: E501
    """get_user_inventory_items

    Returns the inventory items of a specific user by user UUID, paginated. # noqa: E501

    :param get_user_involved_auctions_request: 
    :type get_user_involved_auctions_request: dict | bytes

    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_user_involved_auctions_request = GetUserInvolvedAuctionsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def remove_item(get_inventory_item_request=None):  # noqa: E501
    """remove_item

    Removes a specific item from a user inventory. If item is in an auction, refuses the operation. # noqa: E501

    :param get_inventory_item_request: 
    :type get_inventory_item_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_inventory_item_request = GetInventoryItemRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
