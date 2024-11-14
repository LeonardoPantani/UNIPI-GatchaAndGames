import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def buy_currency(bundle_id, session=None):  # noqa: E501
    """Buy in-game credits

    Allows a player to purchase in-game credits using real-world currency. # noqa: E501

    :param bundle_id: 
    :type bundle_id: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_bundles():  # noqa: E501
    """Lists available bundles to buy currency.

    Returns a list of available bundles # noqa: E501


    :rtype: Union[List[Bundle], Tuple[List[Bundle], int], Tuple[List[Bundle], int, Dict[str, str]]
    """
    return 'do some magic!'
