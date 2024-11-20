import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_info_request import EditUserInfoRequest  # noqa: E501
from openapi_server.models.get_user_hash_psw200_response import GetUserHashPsw200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util


def delete_user_profile(ban_user_profile_request=None):  # noqa: E501
    """delete_user_profile

    Deletes user&#39;s profile and all related data # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def edit_user_info(edit_user_info_request=None):  # noqa: E501
    """edit_user_info

    Modifies user information # noqa: E501

    :param edit_user_info_request: 
    :type edit_user_info_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        edit_user_info_request = EditUserInfoRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_hash_psw(ban_user_profile_request=None):  # noqa: E501
    """get_user_hash_psw

    Returns user&#39;s hashed password # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[GetUserHashPsw200Response, Tuple[GetUserHashPsw200Response, int], Tuple[GetUserHashPsw200Response, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_info(ban_user_profile_request=None):  # noqa: E501
    """get_user_info

    Returns info about a specific user given his UUID # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
