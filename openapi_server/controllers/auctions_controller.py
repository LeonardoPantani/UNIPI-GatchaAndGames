import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.inventory_item_id import InventoryItemId  # noqa: E501
from openapi_server import util


def bid_on_auction(session, auction_uuid, bid):  # noqa: E501
    """Bids on an active auction

    Sends a bid to an active auction, if the user has enough currency. # noqa: E501

    :param session: 
    :type session: str
    :param auction_uuid: Id of the auction to bid on.
    :type auction_uuid: str
    :type auction_uuid: str
    :param bid: Bid value.
    :type bid: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def create_auction(session, gacha_item, starting_price=None):  # noqa: E501
    """Creates an auction.

    Creates an auction for an item in player&#39;s inventory. # noqa: E501

    :param session: 
    :type session: str
    :param gacha_item: The item to sell in the auction.
    :type gacha_item: dict | bytes
    :param starting_price: The starting price of the auction.
    :type starting_price: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha_item =  InventoryItemId.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_auction_status(session, auction_uuid):  # noqa: E501
    """Retrieve info on specific auction.

    Returns info on the auction with a specific id. # noqa: E501

    :param session: 
    :type session: str
    :param auction_uuid: The id of the auction to obtain info
    :type auction_uuid: str
    :type auction_uuid: str

    :rtype: Union[Auction, Tuple[Auction, int], Tuple[Auction, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auctions_history(session, page_number=None):  # noqa: E501
    """Retrieve history of my auctions.

    Returns a list of all my auctions for gacha items. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auctions_list(session, status=None, rarity=None, page_number=None):  # noqa: E501
    """Retrieve the list of auctions.

    Returns a list of all active auctions for gacha items. # noqa: E501

    :param session: 
    :type session: str
    :param status: Filter auctions by status.
    :type status: str
    :param rarity: Filter auctions by type of gacha item.
    :type rarity: dict | bytes
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        rarity =  GachaRarity.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
