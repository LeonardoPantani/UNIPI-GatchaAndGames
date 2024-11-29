import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from pybreaker import CircuitBreaker, CircuitBreakerError
from flask import jsonify, session
import requests
import logging
from datetime import datetime

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server import util

from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)


def delete_match(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def remove_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT *
                FROM pvp_matches
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query,(uuid,))
            if not cursor.fetchone():
                return 404

            query = """
                DELETE 
                FROM pvp_matches
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            connection.commit()
            cursor.close()

            return 200

        status_code = remove_match()

        if status_code == 404:
            return jsonify({"error":"Match not found."}), 404 

        return jsonify({"message":"Match deleted."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503



def get_pending_list(session=None, uuid=None):  # noqa: E501
    """get_pending_list

    Returns the list of pending pvp requests for the user. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[List[PendingPvPRequests], Tuple[List[PendingPvPRequests], int], Tuple[List[PendingPvPRequests], int, Dict[str, str]]
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
