import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.get_inventory_item_request import GetInventoryItemRequest  # noqa: E501
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest  # noqa: E501
from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util


def get_inventory_item(get_inventory_item_request=None):  # noqa: E501
    """get_inventory_item

    Returns detailed information of a specific inventory item for a given user by username and inventory item UUID. # noqa: E501

    :param get_inventory_item_request: 
    :type get_inventory_item_request: dict | bytes

    :rtype: Union[InventoryItem, Tuple[InventoryItem, int], Tuple[InventoryItem, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_inventory_item_request = GetInventoryItemRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


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
