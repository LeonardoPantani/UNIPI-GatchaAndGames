import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.get_gacha_stat200_response import GetGachaStat200Response  # noqa: E501
from openapi_server.models.get_gacha_stat_request import GetGachaStatRequest  # noqa: E501
from openapi_server.models.get_pvp_status_request import GetPvpStatusRequest  # noqa: E501
from openapi_server.models.match_requests_inner import MatchRequestsInner  # noqa: E501
from openapi_server.models.pv_p_request_full import PvPRequestFull  # noqa: E501
from openapi_server.models.reject_pvp_prequest_request import RejectPvpPrequestRequest  # noqa: E501
from openapi_server.models.set_match_results_request import SetMatchResultsRequest  # noqa: E501
from openapi_server.models.verify_gacha_item_ownership_request import VerifyGachaItemOwnershipRequest  # noqa: E501
from openapi_server import util


def check_pending_pvp_requests(ban_user_profile_request=None):  # noqa: E501
    """check_pending_pvp_requests

    Returns a list of pending pvp requests. # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[List[MatchRequestsInner], Tuple[List[MatchRequestsInner], int], Tuple[List[MatchRequestsInner], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def finalize_pvp_request_sending(pv_p_request_full=None):  # noqa: E501
    """finalize_pvp_request_sending

    Inserts a PvP requests. # noqa: E501

    :param pv_p_request_full: 
    :type pv_p_request_full: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pv_p_request_full = PvPRequestFull.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_gacha_stat(get_gacha_stat_request=None):  # noqa: E501
    """get_gacha_stat

    Returns a certain gacha stat for both gachas requested # noqa: E501

    :param get_gacha_stat_request: 
    :type get_gacha_stat_request: dict | bytes

    :rtype: Union[GetGachaStat200Response, Tuple[GetGachaStat200Response, int], Tuple[GetGachaStat200Response, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_gacha_stat_request = GetGachaStatRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_pvp_status(get_pvp_status_request=None):  # noqa: E501
    """get_pvp_status

    Obtains information regarding a pvp match. # noqa: E501

    :param get_pvp_status_request: 
    :type get_pvp_status_request: dict | bytes

    :rtype: Union[PvPRequestFull, Tuple[PvPRequestFull, int], Tuple[PvPRequestFull, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_pvp_status_request = GetPvpStatusRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def reject_pvp_prequest(reject_pvp_prequest_request=None):  # noqa: E501
    """reject_pvp_prequest

    Rejects a pending pvp request. # noqa: E501

    :param reject_pvp_prequest_request: 
    :type reject_pvp_prequest_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        reject_pvp_prequest_request = RejectPvpPrequestRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def set_match_results(set_match_results_request=None):  # noqa: E501
    """set_match_results

    Updates data of pvp_matches setting results. # noqa: E501

    :param set_match_results_request: 
    :type set_match_results_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        set_match_results_request = SetMatchResultsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def verify_gacha_item_ownership(verify_gacha_item_ownership_request=None):  # noqa: E501
    """verify_gacha_item_ownership

    Verifies that a list of gachas separated by a comma is entirely contained in player&#39;s inventory, before letting them send a pvp request. # noqa: E501

    :param verify_gacha_item_ownership_request: 
    :type verify_gacha_item_ownership_request: dict | bytes

    :rtype: Union[str, Tuple[str, int], Tuple[str, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        verify_gacha_item_ownership_request = VerifyGachaItemOwnershipRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
