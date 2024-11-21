import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.get_currency200_response import GetCurrency200Response  # noqa: E501
from openapi_server.models.get_gacha_info_request import GetGachaInfoRequest  # noqa: E501
from openapi_server.models.get_gacha_list_request import GetGachaListRequest  # noqa: E501
from openapi_server.models.give_item_request import GiveItemRequest  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util


def get_gacha_info(get_gacha_info_request=None):  # noqa: E501
    """get_gacha_info

    Returns detailed information about a specific gacha by its UUID. # noqa: E501

    :param get_gacha_info_request: 
    :type get_gacha_info_request: dict | bytes

    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_gacha_info_request = GetGachaInfoRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_gacha_list(get_gacha_list_request=None):  # noqa: E501
    """get_gacha_list

    Inserts the given item into user&#39;s inventory # noqa: E501

    :param get_gacha_list_request: 
    :type get_gacha_list_request: dict | bytes

    :rtype: Union[List[Gacha], Tuple[List[Gacha], int], Tuple[List[Gacha], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_gacha_list_request = GetGachaListRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_pool_info(body=None):  # noqa: E501
    """get_pool_info

    Returns detailed information about a specific gacha pool by its codename # noqa: E501

    :param body: 
    :type body: str

    :rtype: Union[Pool, Tuple[Pool, int], Tuple[Pool, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pools_list():  # noqa: E501
    """get_pools_list

    Inserts the given item into user&#39;s inventory # noqa: E501


    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
    return 'do some magic!'


def give_item(give_item_request=None):  # noqa: E501
    """give_item

    Inserts the given item into user&#39;s inventory # noqa: E501

    :param give_item_request: 
    :type give_item_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        give_item_request = GiveItemRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_currency(ban_user_profile_request=None):  # noqa: E501
    """get_currency

    Returns the currency of a user given the user UUID. # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[GetCurrency200Response, Tuple[GetCurrency200Response, int], Tuple[GetCurrency200Response, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'