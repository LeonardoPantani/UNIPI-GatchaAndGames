import connexion
import logging
from datetime import date
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.edit_user_profile_request import EditUserProfileRequest  # noqa: E501
from openapi_server.models.feedback_preview import FeedbackPreview  # noqa: E501
from openapi_server.models.feedback_with_username import FeedbackWithUsername  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_feedback_info_request import GetFeedbackInfoRequest  # noqa: E501
from openapi_server.models.get_feedback_list_request import GetFeedbackListRequest  # noqa: E501
from openapi_server.models.get_user_history_request import GetUserHistoryRequest  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])

def ban_user_profile(ban_user_profile_request=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    user_uuid = ban_user_profile_request.user_uuid

    mysql = current_app.extensions.get('mysql')

    connection = None
    cursor = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "SELECT role FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            return result

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query 1 ["+ user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query 1 ["+ user_uuid +"]: Programming error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query 1 ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query 1 ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query 1 ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


    user_role = make_request_to_db()

    if user_role:
        if user_role == "ADMIN":
            return "", 409
    else:
        return "", 404
    

    try:
        @circuit_breaker
        def make_request_to_db_2():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute('DELETE FROM feedbacks WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))
            cursor.execute('DELETE FROM ingame_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,)) 
            cursor.execute('DELETE FROM bundles_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))

            cursor.execute('''
                            UPDATE profiles SET currency = currency + (
                                SELECT current_bid
                                FROM auctions
                                WHERE item_uuid IN (
                                    SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                                )
                            )
                            WHERE uuid IN (
                                SELECT current_bidder
                                FROM auctions
                                WHERE item_uuid IN (
                                    SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                                )
                            )
                            ''',
                            (user_uuid, user_uuid)
            )
            
            cursor.execute('UPDATE auctions SET current_bid = 0, current_bidder = NULL WHERE current_bidder = UUID_TO_BIN(%s)', (user_uuid))
            cursor.execute('DELETE FROM pvp_matches WHERE player_1_uuid = UUID_TO_BIN(%s) OR player_2_uuid = UUID_TO_BIN(%s)', (user_uuid,user_uuid))
            cursor.execute('DELETE FROM auctions WHERE item_uuid IN (SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s))', (user_uuid,))
            cursor.execute('DELETE FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)', (user_uuid,))

            query = "DELETE FROM profiles WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (user_uuid,))

            query = "DELETE FROM users WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (user_uuid,))

            connection.commit()

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query 2 ["+ user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query 2 ["+ user_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query 2 ["+ user_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query 2 ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query 2 ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query 2 ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503

    make_request_to_db_2()
    return "", 200
    

def create_gacha_pool(pool=None):  # noqa: E501
    """create_gacha_pool

    Creates a gacha pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_gacha_type(gacha=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501

    # converting letters to numbers for storage
    letters_map = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1
    }
    attributes = ['power', 'speed', 'durability', 'precision', 'range', 'potential']
    converted = {}
    for attr in attributes:
        letter = getattr(gacha.attributes, attr)
        if letter in letters_map:
            converted[attr] = letters_map[letter]
        else:
            converted[attr] = None
    # converted is a map with for each key (stat) a value (numeric of the stat)

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, stat_durability, stat_precision, stat_range, stat_potential, rarity, release_date) VALUES (UUID_TO_BIN(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (gacha.gacha_uuid, gacha.name, converted["power"], converted["speed"], converted["durability"], converted["precision"], converted["range"], converted["potential"], gacha.rarity, date.today()))
            connection.commit()
            return

        make_request_to_db()

        return "", 201
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ gacha.gacha_uuid +"]: Operational error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ gacha.gacha_uuid +"]: Integrity error.")
        return jsonify({"error": "The provided gacha uuid is already in use."}), 409
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ gacha.gacha_uuid +"]: Programming error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ gacha.gacha_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ gacha.gacha_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ gacha.gacha_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503



def delete_gacha_pool(body=None):  # noqa: E501
    """delete_gacha_pool

    Deletes a gacha pool. # noqa: E501

    :param body: 
    :type body: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_gacha_type(body=None):  # noqa: E501
    """delete_gacha_type

    Deletes a gacha type. # noqa: E501

    :param body: 
    :type body: str
    :type body: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def edit_user_profile(edit_user_profile_request=None):  # noqa: E501
    """edit_user_profile

    Edits a user profile. # noqa: E501

    :param edit_user_profile_request: 
    :type edit_user_profile_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        edit_user_profile_request = EditUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_feedback_info(get_feedback_info_request=None):  # noqa: E501
    """get_feedback_info

    Returns info on a single feedback # noqa: E501

    :param get_feedback_info_request: 
    :type get_feedback_info_request: dict | bytes

    :rtype: Union[FeedbackWithUsername, Tuple[FeedbackWithUsername, int], Tuple[FeedbackWithUsername, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_info_request = GetFeedbackInfoRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_feedback_list(get_feedback_list_request=None):  # noqa: E501
    """get_feedback_list

    Gets a feedback list # noqa: E501

    :param get_feedback_list_request: 
    :type get_feedback_list_request: dict | bytes

    :rtype: Union[List[FeedbackPreview], Tuple[List[FeedbackPreview], int], Tuple[List[FeedbackPreview], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_profile_list(get_feedback_list_request=None):  # noqa: E501
    """get_profile_list

    Gets a profile list # noqa: E501

    :param get_feedback_list_request: 
    :type get_feedback_list_request: dict | bytes

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def get_user_history(get_user_history_request=None):  # noqa: E501
    """get_user_history

    Returns history of user&#39;s profile. # noqa: E501

    :param get_user_history_request: 
    :type get_user_history_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_user_history_request = GetUserHistoryRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_auction(auction=None):  # noqa: E501
    """update_auction

    Updates a specific auction. # noqa: E501

    :param auction: 
    :type auction: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_gacha(gacha=None):  # noqa: E501
    """update_gacha

    Updates a specific gacha. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool=None):  # noqa: E501
    """update_pool

    Updates a specific pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
