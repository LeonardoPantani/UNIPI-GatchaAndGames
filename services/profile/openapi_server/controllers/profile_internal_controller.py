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
    """Adds amount to user currency field by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param amount: Amount to add
    :type amount: int
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not amount:
        return "", 400

    try:
        @circuit_breaker
        def update_user_currency():
            connection = get_db()
            cursor = connection.cursor()
            
            # First check if user exists
            check_query = """
            SELECT uuid 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            cursor.execute(check_query, (uuid,))
            if not cursor.fetchone():
                cursor.close()
                return "", 404

            # If user exists, update currency
            query = """
            UPDATE profiles 
            SET currency = currency + %s
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (amount, uuid))
            connection.commit()
            cursor.close()
            return "", 200

        return update_user_currency()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def add_pvp_score(session=None, uuid=None, points_to_add=None):  # noqa: E501
    """Adds amount to user pvp_score field by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param amount: Amount to add
    :type amount: int
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not points_to_add:
        return "", 400

    try:
        @circuit_breaker
        def update_user_pvp_score():
            connection = get_db()
            cursor = connection.cursor()
            
            # Check if user exists
            check_query = """
            SELECT uuid 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            cursor.execute(check_query, (uuid,))
            if not cursor.fetchone():
                cursor.close()
                return "", 404

            # Update pvp score
            query = """
            UPDATE profiles 
            SET pvp_score = pvp_score + %s
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (points_to_add, uuid))
            connection.commit()
            cursor.close()
            return "", 200

        return update_user_pvp_score()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_profile_by_uuid(session=None, uuid=None):  # noqa: E501
    """Deletes user profile by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def delete_user_profile():
            connection = get_db()
            cursor = connection.cursor()
            
            # Check if user exists
            check_query = """
            SELECT uuid 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            cursor.execute(check_query, (uuid,))
            if not cursor.fetchone():
                cursor.close()
                return "", 404

            # Delete profile
            query = """
            DELETE FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            connection.commit()
            cursor.close()
            return "", 200

        return delete_user_profile()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def edit_username(session=None, uuid=None, username=None):  # noqa: E501
    """Edits the username.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param username: New username
    :type username: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not username:
        return "", 400

    try:
        @circuit_breaker
        def update_username():
            connection = get_db()
            cursor = connection.cursor()
            
            # Check if user exists and get current username
            check_query = """
            SELECT username 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            cursor.execute(check_query, (uuid,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return "", 404
                
            # Check if username is the same
            if result[0] == username:
                cursor.close()
                return "", 304
            
            # Update username
            query = """
            UPDATE profiles 
            SET username = %s
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (username, uuid))
            connection.commit()
            cursor.close()
            return "", 200

        return update_username()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_profile(session=None, uuid=None):  # noqa: E501
    """Returns true if a profile exists, false otherwise.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :rtype: Union[ExistsProfile200Response, Tuple[ExistsProfile200Response, int], Tuple[ExistsProfile200Response, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def check_profile_exists():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT uuid
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            return result is not None

        exists = check_profile_exists()
        return jsonify({"exists": exists}), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_currency_from_uuid(session=None, user_uuid=None):  # noqa: E501
    """Returns currency of the requested user.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[GetCurrencyFromUuid200Response, Tuple[GetCurrencyFromUuid200Response, int], Tuple[GetCurrencyFromUuid200Response, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_currency():
            connection = get_db()
            cursor = connection.cursor()
            
            # Check if user exists and get currency
            query = """
            SELECT currency 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if not result:
                return "", 404
                
            return jsonify({"currency": result[0]}), 200

        return get_user_currency()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_profile(session=None, user_uuid=None):  # noqa: E501
    """Returns profile info.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_profile():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT username, currency, pvp_score, created_at
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if not result:
                return "", 404
                
            profile = {
                "username": result[0],
                "currency": result[1],
                "pvp_score": result[2],
                "created_at": result[3].strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return jsonify(profile), 200

        return get_user_profile()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503



def get_username_from_uuid(session=None, user_uuid=None):  # noqa: E501
    """Returns username of the requested user.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[GetUsernameFromUuid200Response, Tuple[GetUsernameFromUuid200Response, int], Tuple[GetUsernameFromUuid200Response, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_username():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT username 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s
            """
            
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            
            if not result:
                return "", 404
                
            return jsonify({"username": result[0]}), 200

        return get_user_username()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503

def get_uuid_from_username(session=None, username=None):  # noqa: E501
    if not username:
        return jsonify({"error": "Invalid request."}), 400
    
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
    """Creates a profile.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :param username: Username
    :type username: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str) or not username:
        return "", 400

    try:
        @circuit_breaker
        def create_profile():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            INSERT INTO profiles (uuid, username, currency, pvp_score, created_at)
            VALUES (UUID_TO_BIN(%s), %s, 0, 0, NOW())
            """
            
            cursor.execute(query, (user_uuid, username))
            connection.commit()
            cursor.close()
            return "", 201

        return create_profile()

    except (OperationalError, DataError,
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except DatabaseError:
        return "", 409
    except IntegrityError:
        return "",409
    except CircuitBreakerError:
        return "", 503


def profile_list(session=None, page_number=None):  # noqa: E501
    """Returns list of profiles based on pagenumber.
    
    :param session: Session cookie
    :type session: str
    :param page_number: Page number of the list
    :type page_number: int
    :rtype: Union[List[UserFull], Tuple[List[UserFull], int], Tuple[List[UserFull], int, Dict[str, str]]]
    """
    # Validate page_number
    if page_number and not isinstance(page_number, (int, str)):
        return "", 400
        
    try:
        page_number = int(page_number) if page_number is not None else 1
        if page_number < 1:
            return "", 400
    except (TypeError, ValueError):
        return "", 400

    try:
        @circuit_breaker
        def get_profiles():
            connection = get_db()
            cursor = connection.cursor()
            
            items_per_page = 10
            offset = (page_number - 1) * items_per_page
            
            query = """
            SELECT BIN_TO_UUID(uuid), username, currency, pvp_score, created_at
            FROM profiles 
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (items_per_page, offset))
            results = cursor.fetchall()
            
            cursor.close()
            
            profiles = []
            for row in results:
                profile = {
                    "uuid": row[0],
                    "username": row[1],
                    "currency": row[2],
                    "pvp_score": row[3],
                    "created_at": row[4].strftime("%Y-%m-%d %H:%M:%S")
                }
                profiles.append(profile)
            
            return jsonify(profiles), 200

        return get_profiles()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503
