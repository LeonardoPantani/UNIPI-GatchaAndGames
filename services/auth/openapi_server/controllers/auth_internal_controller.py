import connexion
import jwt
import redis
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.get_hashed_password200_response import GetHashedPassword200Response
from openapi_server.models.get_role_by_uuid200_response import GetRoleByUuid200Response
from openapi_server.models.get_user200_response import GetUser200Response
from openapi_server.models.user import User
from openapi_server.models.userinfo_request import UserinfoRequest
from openapi_server import util

from flask import jsonify

redis_client = redis.Redis(host='redis', port=6379, db=0)

# Deve essere un oggetto { "AccessToken": "..." }
# Questo ti decripta l'access token e controlla con REDIS che sia lo stesso salvato dall'utente con l'uuid scritto dentro al token
def introspect(userinfo_request=None):
    if not connexion.request.is_json:
        return "", 400

    userinfo_request = UserinfoRequest.from_dict(connexion.request.get_json())
    try:
        decoded_token = jwt.decode(userinfo_request.access_token, "prova", algorithms=["HS256"], audience="public_services")
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"]
        }

        saved_token = redis_client.get(decoded_token["uuid"]).decode("utf-8")

        if saved_token is not None and saved_token != userinfo_request.access_token:
            return jsonify({"error": "Unauthorized."}), 401

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired."}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Unauthorized."}), 401

# Deve essere un oggetto { "AccessToken": "..." }
# Questa funzione ti decripta l'AccessToken e basta, senza altri controlli
def userinfo(userinfo_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    userinfo_request = UserinfoRequest.from_dict(connexion.request.get_json())
    
    try:
        decoded_token = jwt.decode(userinfo_request.access_token, "prova", algorithms=["HS256"], audience="public_services")
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"]
        }

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


def delete_user_by_uuid(session=None, uuid=None):
    """delete_user_by_uuid

    Deletes a user. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def edit_email(session=None, uuid=None, email=None):
    """edit_email

    Updates a user&#39;s email. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str
    :param email: 
    :type email: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_hashed_password(session=None, uuid=None):
    """get_hashed_password

    Returns user hashed password. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[GetHashedPassword200Response, Tuple[GetHashedPassword200Response, int], Tuple[GetHashedPassword200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_role_by_uuid(session=None, uuid=None):
    """get_role_by_uuid

    Returns role of the user by UUID, if exists. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[GetRoleByUuid200Response, Tuple[GetRoleByUuid200Response, int], Tuple[GetRoleByUuid200Response, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user(session=None, uuid=None):
    """get_user

    Returns user info. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str
    :type uuid: str

    :rtype: Union[GetUser200Response, Tuple[GetUser200Response, int], Tuple[GetUser200Response, int, Dict[str, str]]
    """
    return 'do some magic!'