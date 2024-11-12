import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.delete_profile_request import DeleteProfileRequest  # noqa: E501
from openapi_server.models.edit_profile_request import EditProfileRequest  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util


def delete_profile(delete_profile_request, session=None):  # noqa: E501
    """Deletes this account.

    Allows a user to delete their account. # noqa: E501

    :param delete_profile_request: 
    :type delete_profile_request: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        delete_profile_request = DeleteProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def edit_profile(edit_profile_request, session=None):  # noqa: E501
    """Edits properties of the profile.

    Allows a user to edit their profile. # noqa: E501

    :param edit_profile_request: 
    :type edit_profile_request: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        edit_profile_request = EditProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_info(uuid):  # noqa: E501
    """Returns infos about a UUID.

    Allows to retrieve the profile of a user by UUID. # noqa: E501

    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'
