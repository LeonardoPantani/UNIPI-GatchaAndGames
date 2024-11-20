import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_profile_request import EditUserProfileRequest  # noqa: E501
from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_feedback_info_request import GetFeedbackInfoRequest  # noqa: E501
from openapi_server.models.get_feedback_list_request import GetFeedbackListRequest  # noqa: E501
from openapi_server.models.get_user_history_request import GetUserHistoryRequest  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util


def ban_user_profile(ban_user_profile_request=None):  # noqa: E501
    """ban_user_profile

    Bans a user from the platform. Cannot ban another ADMIN. # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_gacha_pool(pool=None):  # noqa: E501
    """create_gacha_pool

    Creates a gacha pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_gacha_type(gacha=None):  # noqa: E501
    """create_gacha_type

    Creates a gacha type. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_gacha_pool(body=None):  # noqa: E501
    """delete_gacha_pool

    Deletes a gacha pool. # noqa: E501

    :param body: 
    :type body: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_gacha_type(body=None):  # noqa: E501
    """delete_gacha_type

    Deletes a gacha type. # noqa: E501

    :param body: 
    :type body: str
    :type body: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def edit_user_profile(edit_user_profile_request=None):  # noqa: E501
    """edit_user_profile

    Edits a user profile. # noqa: E501

    :param edit_user_profile_request: 
    :type edit_user_profile_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        edit_user_profile_request = EditUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_feedback_info(get_feedback_info_request=None):  # noqa: E501
    """get_feedback_info

    Returns info on a single feedback # noqa: E501

    :param get_feedback_info_request: 
    :type get_feedback_info_request: dict | bytes

    :rtype: Union[FeedbackWithUsername, Tuple[FeedbackWithUsername, int], Tuple[FeedbackWithUsername, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_info_request = GetFeedbackInfoRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_feedback_list(get_feedback_list_request=None):  # noqa: E501
    """get_feedback_list

    Gets a feedback list # noqa: E501

    :param get_feedback_list_request: 
    :type get_feedback_list_request: dict | bytes

    :rtype: Union[List[FeedbackPreview], Tuple[List[FeedbackPreview], int], Tuple[List[FeedbackPreview], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_profile_list(get_feedback_list_request=None):  # noqa: E501
    """get_profile_list

    Gets a profile list # noqa: E501

    :param get_feedback_list_request: 
    :type get_feedback_list_request: dict | bytes

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_history(get_user_history_request=None):  # noqa: E501
    """get_user_history

    Returns history of user&#39;s profile. # noqa: E501

    :param get_user_history_request: 
    :type get_user_history_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_user_history_request = GetUserHistoryRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_auction(auction=None):  # noqa: E501
    """update_auction

    Updates a specific auction. # noqa: E501

    :param auction: 
    :type auction: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_gacha(gacha=None):  # noqa: E501
    """update_gacha

    Updates a specific gacha. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool=None):  # noqa: E501
    """update_pool

    Updates a specific pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
