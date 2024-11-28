import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests_inner import PendingPvPRequestsInner  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server import util


def delete_match(session=None, uuid=None):  # noqa: E501
    """delete_match

    Deletes a pvp match. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pending_list(session=None, uuid=None):  # noqa: E501
    """get_pending_list

    Returns the list of pending pvp requests for the user. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[List[List[PendingPvPRequestsInner]], Tuple[List[List[PendingPvPRequestsInner]], int], Tuple[List[List[PendingPvPRequestsInner]], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_status(session=None, uuid=None):  # noqa: E501
    """get_status

    Returns info on a pvp match. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[PvPRequest, Tuple[PvPRequest, int], Tuple[PvPRequest, int, Dict[str, str]]
    """
    return 'do some magic!'


def insert_match(pv_p_request, session=None):  # noqa: E501
    """insert_match

    Inserts a match into the database. # noqa: E501

    :param pv_p_request: 
    :type pv_p_request: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pv_p_request = PvPRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def remove_by_user_uuid(session=None, uuid=None):  # noqa: E501
    """remove_by_user_uuid

    Deletes matches where user with UUID as requested appears. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def set_results(pv_p_request, session=None):  # noqa: E501
    """set_results

    Inserts match results into the database. # noqa: E501

    :param pv_p_request: 
    :type pv_p_request: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pv_p_request = PvPRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
