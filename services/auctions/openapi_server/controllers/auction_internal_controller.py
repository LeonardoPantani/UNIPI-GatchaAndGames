import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.auction_status import AuctionStatus  # noqa: E501
from openapi_server.models.exists_auctions200_response import ExistsAuctions200Response  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.is_open_by_item_uuid200_response import IsOpenByItemUuid200Response  # noqa: E501
from openapi_server import util


def create_auction(auction, session=None):  # noqa: E501
    """create_auction

    Inserts new auction into db. # noqa: E501

    :param auction: 
    :type auction: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def exists_auctions(session=None, uuid=None):  # noqa: E501
    """exists_auctions

    Returns true if an auction exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[ExistsAuctions200Response, Tuple[ExistsAuctions200Response, int], Tuple[ExistsAuctions200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auction(session=None, uuid=None):  # noqa: E501
    """get_auction

    Returns information of an auction by its uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[Auction, Tuple[Auction, int], Tuple[Auction, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auction_list(session=None, status=None, rarity=None, page_number=None):  # noqa: E501
    """get_auction_list

    Returns the list of auctions filtered by status and rarity, organized in pages # noqa: E501

    :param session: 
    :type session: str
    :param status: 
    :type status: dict | bytes
    :param rarity: 
    :type rarity: dict | bytes
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[Auction], Tuple[List[Auction], int], Tuple[List[Auction], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        status =  AuctionStatus.from_dict(connexion.request.get_json())  # noqa: E501
    if connexion.request.is_json:
        rarity =  GachaRarity.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_auctions(session=None, user_uuid=None):  # noqa: E501
    """get_user_auctions

    Returns list of auctions where user is the owner of the item or the current highest bidder. # noqa: E501

    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str

    :rtype: Union[List[Auction], Tuple[List[Auction], int], Tuple[List[Auction], int, Dict[str, str]]
    """
    return 'do some magic!'


def is_open_by_item_uuid(session=None, uuid=None):  # noqa: E501
    """is_open_by_item_uuid

    Returns true if an open auction is found, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[IsOpenByItemUuid200Response, Tuple[IsOpenByItemUuid200Response, int], Tuple[IsOpenByItemUuid200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def refund_bidders(request_body, session=None):  # noqa: E501
    """refund_bidders

    Returns inventory items owned by user with UUID requested. # noqa: E501

    :param request_body: List of the item_uuid whose eventual auctions must be refunded to eventual bidders.
    :type request_body: List[str]
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def remove_by_item_uuid(request_body, session=None):  # noqa: E501
    """remove_by_item_uuid

    Deletes eventual auctions where item_uuid is in list. # noqa: E501

    :param request_body: List of the item_uuid whose eventual auctions must be deleted.
    :type request_body: List[str]
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def reset_current_bidder(session=None, uuid=None):  # noqa: E501
    """reset_current_bidder

    Sets current bid to 0 and current bidder to NULL. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def set_bid(session=None, auction_uuid=None, user_uuid=None, new_bid=None):  # noqa: E501
    """set_bid

    Updates current bid and current bidder. # noqa: E501

    :param session: 
    :type session: str
    :param auction_uuid: 
    :type auction_uuid: str
    :type auction_uuid: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param new_bid: 
    :type new_bid: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def update_auction(session=None, auction=None):  # noqa: E501
    """update_auction

    Updates an auction. # noqa: E501

    :param session: 
    :type session: str
    :param auction: 
    :type auction: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
