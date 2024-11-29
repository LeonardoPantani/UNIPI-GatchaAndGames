import connexion
import logging
import requests
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.exists_profile200_response import ExistsProfile200Response  # noqa: E501
from openapi_server.models.get_currency_from_uuid200_response import GetCurrencyFromUuid200Response  # noqa: E501
from openapi_server.models.get_username_from_uuid200_response import GetUsernameFromUuid200Response  # noqa: E501
from openapi_server.models.get_uuid_from_username200_response import GetUuidFromUsername200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server.models.user_full import UserFull  # noqa: E501
from openapi_server import util

from flask import session, jsonify
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])

def add_currency(session=None, uuid=None, amount=None):  # noqa: E501
    """add_currency

    Adds amount to user currency field by uuid. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param amount: 
    :type amount: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def add_pvp_score(session=None, uuid=None, points_to_add=None):  # noqa: E501
    """add_pvp_score

    Increases pvp score by points value. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param points_to_add: 
    :type points_to_add: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_profile_by_uuid(session=None, uuid=None):  # noqa: E501
    """delete_profile_by_uuid

    Deletes a user&#39;s profile. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def edit_username(session=None, uuid=None, username=None):  # noqa: E501
    """edit_username

    Edits the username. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param username: 
    :type username: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def exists_profile(session=None, uuid=None):  # noqa: E501
    """exists_profile

    Returns true if a profile exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[ExistsProfile200Response, Tuple[ExistsProfile200Response, int], Tuple[ExistsProfile200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_currency_from_uuid(session=None, user_uuid=None):  # noqa: E501
    """get_currency_from_uuid

    Returns currency of the requested user. # noqa: E501

    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str

    :rtype: Union[GetCurrencyFromUuid200Response, Tuple[GetCurrencyFromUuid200Response, int], Tuple[GetCurrencyFromUuid200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_profile(session=None, user_uuid=None):  # noqa: E501
    """get_profile

    Returns profile info. # noqa: E501

    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_username_from_uuid(session=None, user_uuid=None):  # noqa: E501

    return jsonify({"username": "suka"}), 200

def get_uuid_from_username(session=None, username=None):  # noqa: E501
    if not username:
        return "", 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT BIN_TO_UUID(uuid) as uuid
                FROM profiles
                WHERE username = %s
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()
        
        result = make_request_to_db()

        if not result:
            return "", 404
        return result["uuid"]

    except OperationalError:
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query: Database error.")
        return "", 500


def insert_profile(session=None, user_uuid=None, username=None):  # noqa: E501
    """insert_profile

    Creates a profile. # noqa: E501

    :param session: 
    :type session: str
    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param username: 
    :type username: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def profile_list(session=None, page_number=None):  # noqa: E501
    """profile_list

    Returns list of profiles based on pagenumber. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[UserFull], Tuple[List[UserFull], int], Tuple[List[UserFull], int, Dict[str, str]]
    """
    return 'do some magic!'
