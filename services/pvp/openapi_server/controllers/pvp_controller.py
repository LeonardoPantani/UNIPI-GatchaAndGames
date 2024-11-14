import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server.models.team import Team  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def accept_pvp_request(pvp_match_uuid, team, session=None):  # noqa: E501
    """Accept a pending PvP request.

    Allows a player to accept a PvP battle with another user. # noqa: E501

    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str
    :param team: Specify the team to battle the player with.
    :type team: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        team = Team.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def check_pending_pvp_requests(session=None):  # noqa: E501
    """Returns a list of pending PvP requests.

    If the current user has one or more pending requests, a list will be returned. The current user&#39;s UUID is obtained via session cookie. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[PendingPvPRequests, Tuple[PendingPvPRequests, int], Tuple[PendingPvPRequests, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pvp_status(pvp_match_uuid, session=None):  # noqa: E501
    """Returns the results of a PvP match.

    Allows a player to view the results of the match. # noqa: E501

    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[PvPRequest, Tuple[PvPRequest, int], Tuple[PvPRequest, int, Dict[str, str]]
    """
    return 'do some magic!'


def reject_pv_prequest(pvp_match_uuid, session=None):  # noqa: E501
    """Rejects a pending PvP request.

    Allows a player to reject a PvP battle with another user. # noqa: E501

    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def send_pvp_request(user_uuid, team, session=None):  # noqa: E501
    """Sends a PvP match request.

    Sends a requests to another player to initiate a PvP battle. # noqa: E501

    :param user_uuid: The player&#39;s UUID to send the battle request to.
    :type user_uuid: str
    :type user_uuid: str
    :param team: Specify the team to battle the player with.
    :type team: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[PvPRequest, Tuple[PvPRequest, int], Tuple[PvPRequest, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        team = Team.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
