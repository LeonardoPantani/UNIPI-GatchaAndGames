from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.login_request import LoginRequest  # noqa: E501
from openapi_server.models.register_request import RegisterRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify
from flaskext.mysql import MySQL
import connexion

def login():
    if connexion.request.is_json:
        login_request = connexion.request.get_json()
        username = login_request.get("username")
        password = login_request.get("password")

        try:
            mysql = current_app.extensions.get('mysql')
            
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500
                
            cursor = mysql.connect().cursor()
            cursor.execute('SELECT * FROM USERS')
            result = cursor.fetchone()
            cursor.close()
            
            return jsonify({
                "message": "Database connection successful",
                "result": result
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Invalid request"}), 400

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
