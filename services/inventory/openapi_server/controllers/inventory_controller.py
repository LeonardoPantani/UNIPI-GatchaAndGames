import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util


def get_inventory(session=None, page_number=None):  # noqa: E501
    """Retrieve player&#39;s inventory

    Returns a list of gacha items currently owned by the player. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_inventory_item_info(inventory_item_id, session=None):  # noqa: E501
    """Shows infos on my inventory item.

    Returns infos on my inventory item. # noqa: E501

    :param inventory_item_id: 
    :type inventory_item_id: str
    :type inventory_item_id: str
    :param session: 
    :type session: str

    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    return 'do some magic!'


def remove_inventory_item(session=None, inventory_item_owner_id=None, inventory_item_id=None):  # noqa: E501
    """Removes an item from player&#39;s inventory

    Returns a list of gacha items currently owned by the player. # noqa: E501

    :param session: 
    :type session: str
    :param inventory_item_owner_id: 
    :type inventory_item_owner_id: str
    :type inventory_item_owner_id: str
    :param inventory_item_id: 
    :type inventory_item_id: str
    :type inventory_item_id: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'
