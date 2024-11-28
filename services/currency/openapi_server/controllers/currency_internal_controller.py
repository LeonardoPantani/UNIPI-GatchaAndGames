import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server.models.get_user_history200_response import GetUserHistory200Response  # noqa: E501
from openapi_server import util


def delete_user_transactions(session=None, uuid=None):  # noqa: E501
    """delete_user_transactions

    Deletes transaction made by the user by UUID, if exist. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_bundle(session=None, codename=None):  # noqa: E501
    """get_bundle

    Returns requested bundle info. # noqa: E501

    :param session: 
    :type session: str
    :param codename: 
    :type codename: str

    :rtype: Union[Bundle, Tuple[Bundle, int], Tuple[Bundle, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user_history(session=None, uuid=None, history_type=None, page_number=None):  # noqa: E501
    """Returns history of a user.

    Allows to retrieve history of a user. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param history_type: Type of history to show.
    :type history_type: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[GetUserHistory200Response, Tuple[GetUserHistory200Response, int], Tuple[GetUserHistory200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def insert_bundle_transaction(session=None, uuid=None, bundle_codename=None, currency_name=None):  # noqa: E501
    """insert_bundle_transaction

    Inserts transaction of ingame currency. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param bundle_codename: Codename of the bundle.
    :type bundle_codename: str
    :param currency_name: Type of transaction.
    :type currency_name: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def insert_ingame_transaction(session=None, uuid=None, current_bid=None, transaction_type=None):  # noqa: E501
    """insert_ingame_transaction

    Inserts transaction of ingame currency. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param current_bid: Amount of currency spent.
    :type current_bid: int
    :param transaction_type: Type of transaction.
    :type transaction_type: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def list_bundles(session=None):  # noqa: E501
    """list_bundles

    Returns bundle list. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[List[Bundle], Tuple[List[Bundle], int], Tuple[List[Bundle], int, Dict[str, str]]
    """
    return 'do some magic!'
