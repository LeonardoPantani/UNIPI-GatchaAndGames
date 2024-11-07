import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from flask import jsonify

from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server import util


def login():  # Rimuovi il parametro 'login_request'
    if connexion.request.is_json:
        login_request = connexion.request.get_json()  # Ottieni il JSON direttamente dalla richiesta
        username = login_request.get("username")
        password = login_request.get("password")


        # Logica di autenticazione qui...
        return jsonify(message="Login successful"), 200  # Esempio di risposta positiva
    return jsonify(message="Invalid request"), 400


def logout(session):  # noqa: E501
    """Logs out from an account.

    Allows an account to log out. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def register(register_request):  # noqa: E501
    """Registers a new account.

    Registers a new user account with username, email, and password. # noqa: E501

    :param register_request: 
    :type register_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    return 'do some magic!'
