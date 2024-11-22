import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_info_request import EditUserInfoRequest  # noqa: E501
from openapi_server.models.get_user_hash_psw200_response import GetUserHashPsw200Response  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging

# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def delete_user_profile(ban_user_profile_request=None):  # noqa: E501
    """delete_user_profile

    Deletes user&#39;s profile and all related data # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def edit_user_info(edit_user_info_request=None):
    """
    Modifies user information
    
    :param edit_user_info_request: Request object containing user info to update
    :return: Status code and message
    """
    if not connexion.request.is_json:
        return "", 400
    
    # Parse request
    edit_user_info_request = EditUserInfoRequest.from_dict(connexion.request.get_json())
    user_uuid = edit_user_info_request.user_uuid
    email = edit_user_info_request.email
    username = edit_user_info_request.username

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            updates = 0
            connection = mysql.connect()
            cursor = connection.cursor()
            
            # Check if user exists
            cursor.execute(
                'SELECT 1 FROM users WHERE uuid = UUID_TO_BIN(%s)',
                (user_uuid,)
            )
            if not cursor.fetchone():
                return None
            
            # Update user information if provided
            updates=0

            if email:
                cursor.execute(
                    'UPDATE users SET email = %s WHERE uuid = UUID_TO_BIN(%s)',
                    (email, user_uuid)
                )
                updates += cursor.rowcount
                
            if username:
                cursor.execute(
                    'UPDATE profiles SET username = %s WHERE uuid = UUID_TO_BIN(%s)',
                    (username, user_uuid)
                )
                updates += cursor.rowcount
                
            connection.commit()
            return updates

        result = make_request_to_db()
        
        if result is None:
            return "", 404
            
        if result == 0:
            return "", 304  # No changes made
            
        return "", 200

    except OperationalError:
        logging.error(f"Query [{user_uuid}]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error(f"Query [{user_uuid}]: Programming error.")
        return "", 400
    except IntegrityError:
        logging.error(f"Query [{user_uuid}]: Integrity error.")
        return "", 409
    except InternalError:
        logging.error(f"Query [{user_uuid}]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error(f"Query [{user_uuid}]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error(f"Query [{user_uuid}]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet")
        return "", 503


def get_user_hash_psw(ban_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # Parse request
    ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())
    user_uuid = ban_user_profile_request.user_uuid

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT password FROM users WHERE uuid = UUID_TO_BIN(%s)',
                (user_uuid,)
            )
            return cursor.fetchone()

        result = make_request_to_db()

        if not result:
            return "", 404

        return jsonify({"password": result[0]}), 200

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid +"]: Integrity error.") 
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server 
        logging.error("Query ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_info(ban_user_profile_request=None):  # noqa: E501
    """get_user_info

    Returns info about a specific user given his UUID # noqa: E501

    :param ban_user_profile_request: 
    :type ban_user_profile_request: dict | bytes

    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
