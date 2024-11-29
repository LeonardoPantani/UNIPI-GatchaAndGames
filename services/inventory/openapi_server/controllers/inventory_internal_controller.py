import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import jsonify, session
import requests
import redis
import logging

from openapi_server.models.check_owner_of_team_request import CheckOwnerOfTeamRequest  # noqa: E501
from openapi_server.models.exists_inventory200_response import ExistsInventory200Response  # noqa: E501
from openapi_server.models.get_stand_uuid_by_item_uuid200_response import GetStandUuidByItemUuid200Response  # noqa: E501
from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util
from pybreaker import CircuitBreaker, CircuitBreakerError

from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db



from openapi_server.helpers.authorization import verify_login

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def check_owner_of_team(check_owner_of_team_request, session=None, user_uuid=None):  # noqa: E501
    """Checks if a team is actually owned by the user."""
    session = verify_login(connexion.request.headers.get('Authorization'))

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    check_owner_of_team_request = CheckOwnerOfTeamRequest.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        @circuit_breaker
        def verify_team_ownership():
            connection = get_db()
            cursor = connection.cursor()
            
            team_uuids = tuple(check_owner_of_team_request.team)
            expected_count = len(team_uuids)
            
            # Query to check if all items in team belong to user
            query = """
            SELECT COUNT(DISTINCT item_uuid) 
            FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s 
            AND BIN_TO_UUID(item_uuid) IN %s
            HAVING COUNT(DISTINCT item_uuid) = %s
            """

            cursor.execute(query, (user_uuid, team_uuids,expected_count))
            result = cursor.fetchone()[0]
            
            cursor.close()
            return result is not None and result[0] == expected_count

        items_owned = verify_team_ownership()
        
        if not items_owned:
            return jsonify({"error": "Items not found in user inventory."}), 404
            
        return jsonify({"message": "Items verified."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_by_stand_uuid(session=None, uuid=None):  # noqa: E501
    """delete_by_stand_uuid

    Deletes items which are a certain stand. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_user_inventory(session=None, uuid=None):  # noqa: E501
    """delete_user_inventory

    Deletes items owned by user. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def exists_inventory(session=None, uuid=None):  # noqa: E501
    """exists_inventory

    Returns true if an item exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[ExistsInventory200Response, Tuple[ExistsInventory200Response, int], Tuple[ExistsInventory200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_gachas_types_of_user(session=None, user_uuid=None):  # noqa: E501
    """get_gachas_types_of_user

    Returns list of stands types owned by the user. # noqa: E501

    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_inventory_by_owner_uuid(session=None, uuid=None):  # noqa: E501
    """get_inventory_by_owner_uuid

    Returns inventory items owned by user with UUID requested. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_inventory_items_by_owner_uuid(session=None, uuid=None, page_number=None):  # noqa: E501
    """get_inventory_items_by_owner_uuid

    Returns inventory items owned by user with UUID requested, paginated. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_item_by_uuid(session=None, uuid=None):  # noqa: E501
    """get_item_by_uuid

    Returns item with requested uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[InventoryItem, Tuple[InventoryItem, int], Tuple[InventoryItem, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_items_by_stand_uuid(session=None, uuid=None):  # noqa: E501
    """get_items_by_stand_uuid

    Returns list of items which are a specific stand. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_stand_uuid_by_item_uuid(session=None, uuid=None):  # noqa: E501
    """get_stand_uuid_by_item_uuid

    Returns item with requested uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[GetStandUuidByItemUuid200Response, Tuple[GetStandUuidByItemUuid200Response, int], Tuple[GetStandUuidByItemUuid200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def insert_item(inventory_item, session=None):  # noqa: E501
    """insert_item

    Assigns a certain item. # noqa: E501

    :param inventory_item: 
    :type inventory_item: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        inventory_item = InventoryItem.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def remove_item(session=None, item_uuid=None, owner_uuid=None):  # noqa: E501
    """remove_item

    Removes item from inventory, by item and owner UUID. # noqa: E501

    :param session: 
    :type session: str
    :param item_uuid: 
    :type item_uuid: str
    :type item_uuid: str
    :param owner_uuid: 
    :type owner_uuid: str
    :type owner_uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def update_item_ownership(session=None, new_owner_uuid=None, item_uuid=None, price_paid=None):  # noqa: E501
    """update_item_ownership

    Updates ownership of a certain item. # noqa: E501

    :param session: 
    :type session: str
    :param new_owner_uuid: 
    :type new_owner_uuid: str
    :type new_owner_uuid: str
    :param item_uuid: 
    :type item_uuid: str
    :type item_uuid: str
    :param price_paid: 
    :type price_paid: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'
