import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_all_feedbacks200_response_inner import GetAllFeedbacks200ResponseInner  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL


def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def ban_profile(user_uuid, session=None):  # noqa: E501
    """Deletes a profile.

    Allows an admin to delete a user&#39;s profile. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def create_gacha(gacha, session=None):  # noqa: E501
    """Creates a gacha.

    Allows the creation of a gacha. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_pool(pool, session=None):  # noqa: E501
    """Creates a pool.

    Allows the creation of a pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def delete_gacha(gacha_uuid, session=None):  # noqa: E501
    """Deletes a gacha.

    Allows the deletion of a gacha. # noqa: E501

    :param gacha_uuid: 
    :type gacha_uuid: str
    :type gacha_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_pool(pool_id, session=None):  # noqa: E501
    """Deletes a pool.

    Allows the deletion of a pool. # noqa: E501

    :param pool_id: 
    :type pool_id: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def edit_user_profile(user_uuid, session=None, email=None, username=None):  # noqa: E501
    """Edits properties of a profile.

    Allows an admin to edit a user&#39;s profile. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param session: 
    :type session: str
    :param email: 
    :type email: str
    :param username: 
    :type username: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_all_feedbacks(session=None, page_number=None):  # noqa: E501
    """Returns all feedbacks.

    Allows to retrieve all feedbacks, paginated. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[GetAllFeedbacks200ResponseInner], Tuple[List[GetAllFeedbacks200ResponseInner], int], Tuple[List[GetAllFeedbacks200ResponseInner], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_all_profiles(session=None, page_number=None):  # noqa: E501
    """Returns all profiles.

    Allows to retrieve all profiles, paginated. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feedback(feedback_id, session=None):  # noqa: E501
    """Returns a feedback by id.

    Allows to read a specific feedback. # noqa: E501

    :param feedback_id: Id of feedback.
    :type feedback_id: int
    :param session: 
    :type session: str

    :rtype: Union[str, Tuple[str, int], Tuple[str, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_system_logs(session=None):  # noqa: E501
    """Returns the system logs.

    Allows to retrieve logs of the system. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user_history(user_uuid, type, session=None, page_number=None):  # noqa: E501
    """Returns history of a user.

    Allows to retrieve history of a user. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param type: Type of history to show.
    :type type: str
    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def update_auction(auction_uuid, auction, session=None):  # noqa: E501
    """Updates an auction.

    Allows the update of an auction. # noqa: E501

    :param auction_uuid: 
    :type auction_uuid: str
    :type auction_uuid: str
    :param auction: 
    :type auction: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_gacha(gacha_uuid, gacha, session=None):  # noqa: E501
    """Updates a gacha.

    Allows the update of a gacha. # noqa: E501

    :param gacha_uuid: 
    :type gacha_uuid: str
    :type gacha_uuid: str
    :param gacha: 
    :type gacha: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool_id, pool, session=None):  # noqa: E501
    """Updates a pool.

    Allows the update of a pool. # noqa: E501

    :param pool_id: 
    :type pool_id: str
    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
