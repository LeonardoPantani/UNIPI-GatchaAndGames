import connexion
import logging
import json
from datetime import date
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest
from openapi_server.models.edit_user_profile_request import EditUserProfileRequest
from openapi_server.models.feedback_preview import FeedbackPreview
from openapi_server.models.feedback_with_username import FeedbackWithUsername
from openapi_server.models.gacha import Gacha
from openapi_server.models.get_feedback_info_request import GetFeedbackInfoRequest
from openapi_server.models.get_feedback_list_request import GetFeedbackListRequest
from openapi_server.models.get_user_history_request import GetUserHistoryRequest
from openapi_server.models.pool import Pool
from openapi_server.models.user import User
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])

def ban_user_profile(ban_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())
    user_uuid = ban_user_profile_request.user_uuid

    mysql = current_app.extensions.get('mysql')

    connection = None
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
    

def create_gacha_pool(pool=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    pool = Pool.from_dict(connexion.request.get_json())

    probabilities = {
        "common": pool.probabilities.common_probability,
        "rare": pool.probabilities.rare_probability,
        "epic": pool.probabilities.epic_probability,
        "legendary":  pool.probabilities.legendary_probability,
    }
    
    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "INSERT INTO gacha_pools (codename, public_name, probabilities, price) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (pool.id, pool.name, json.dumps(probabilities), pool.price))
            for gacha_type_uuid in pool.items:
                query = "INSERT INTO gacha_pools (codename, gacha_uuid) VALUES (%s, %s)"
                cursor.execute(query, (pool.id, gacha_type_uuid))
            connection.commit()
            return

        make_request_to_db()

        return "", 201
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ pool.id +"]: Operational error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ pool.id +"]: Integrity error.")
        return "", 409
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ pool.id +"]: Programming error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ pool.id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ pool.id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ pool.id +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def create_gacha_type(gacha=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    gacha = Gacha.from_dict(connexion.request.get_json())

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


def delete_gacha_pool(body=None): # TODO controllare dipendenze tra elementi nel db
    """delete_gacha_pool

    Deletes a gacha pool. # noqa: E501

    :param body: 
    :type body: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def delete_gacha_type(): # TODO controllare dipendenze tra elementi nel db
    if not connexion.request.is_json:
        return "", 400

    mysql = current_app.extensions.get('mysql')

    gacha_uuid = connexion.request.get_json()

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()

            delete_query = "DELETE FROM gacha_pools_items WHERE gacha_uuid = UUID_TO_BIN(%s)"
            cursor.execute(delete_query, (gacha_uuid,))
            delete_query = "DELETE FROM inventories WHERE stand_uuid = UUID_TO_BIN(%s)"
            cursor.execute(delete_query, (gacha_uuid,))
            delete_query = "DELETE FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(delete_query, (gacha_uuid,))
            connection.commit()
            return cursor.rowcount

        if make_request_to_db() == 0:
            return jsonify({"error": "Gacha not found."}), 404

        return "", 201
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ gacha_uuid +"]: Operational error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ gacha_uuid +"]: Integrity error.")
        return "", 409
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ gacha_uuid +"]: Programming error.")
        return "", 400
    except DataError:
        logging.error("Query ["+ gacha_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ gacha_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ gacha_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ gacha_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def edit_user_profile(edit_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    edit_user_profile_request = EditUserProfileRequest.from_dict(connexion.request.get_json())

    user_uuid = edit_user_profile_request.uuid
    user_email = edit_user_profile_request.email
    username = edit_user_profile_request.username
    
    mysql = current_app.extensions.get('mysql')


    try:
        # to discriminate which request failed outside the function make_request_to_db()
        not_found = False

        @circuit_breaker
        def make_request_to_db():
            global not_found
            updates = 0

            connection = mysql.connect()
            cursor = connection.cursor()
            # check if profile with that uuid exists
            query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            if not result:
                not_found = True
                return updates

            # user exists, continue
            if user_email:
                query = "UPDATE users SET email = %s WHERE uuid = UUID_TO_BIN(%s)"
                cursor.execute(query, (user_email, user_uuid))
                updates += cursor.rowcount
            if username:
                query = "UPDATE profiles SET username = %s WHERE uuid = UUID_TO_BIN(%s)"
                cursor.execute(query, (username, user_uuid))
                updates += cursor.rowcount
                
            connection.commit()
            return updates

        updates = make_request_to_db()

        if not_found:
            return "", 404
        
        if updates == 0:
            return "", 203
        
        return "", 200

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
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_feedback_info(get_feedback_info_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    get_feedback_info_request = GetFeedbackInfoRequest.from_dict(connexion.request.get_json())
    feedback_id = get_feedback_info_request.feedback_id
    
    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "SELECT f.id, BIN_TO_UUID(f.user_uuid) as uuid, f.content, f.timestamp, p.username FROM feedbacks f JOIN profiles p ON f.user_uuid = p.uuid WHERE id = %s"
            cursor.execute(query, (feedback_id,))
            return cursor.fetchone()

        feedback = make_request_to_db()
        
        if feedback:
            feedback_info = {"id": feedback[0], "user_uuid": feedback[1], "content": feedback[2], "timestamp": feedback[3], "username": feedback[4]}
            return jsonify(feedback_info), 200
        else:
            return "", 404

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ feedback_id +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ feedback_id +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ feedback_id +"]: Integrity error.")
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ feedback_id +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ feedback_id +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ feedback_id +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503

    return 'do some magic!'


def get_feedback_list(get_feedback_list_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())
    page_number = get_feedback_list_request.page_number
    offset = (page_number - 1) * 10 if page_number else 0
    
    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "SELECT f.id, BIN_TO_UUID(f.user_uuid), f.timestamp FROM feedbacks f LIMIT 10 OFFSET %s"
            cursor.execute(query, (offset,))
            return cursor.fetchall()

        feedbacks = make_request_to_db()
        feedback_list = [
            {"id": feedback[0], "user_uuid": feedback[1], "timestamp": str(feedback[2])}
            for feedback in feedbacks
        ]
        return jsonify(feedback_list), 200

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ page_number +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ page_number +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ page_number +"]: Integrity error.")
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ page_number +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ page_number +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ page_number +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_profile_list(get_feedback_list_request=None):
    if not connexion.request.is_json:
        return "", 400

    # valid json request
    get_feedback_list_request = GetFeedbackListRequest.from_dict(connexion.request.get_json())
    page_number = get_feedback_list_request.page_number
    offset = (page_number - 1) * 10 if page_number else 0
    
    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "SELECT BIN_TO_UUID(p.uuid) as uuid, u.email, p.username, p.currency, p.pvp_score, p.created_at, u.role FROM profiles p JOIN users u ON p.uuid = u.uuid LIMIT 10 OFFSET %s"
            cursor.execute(query, (offset,))
            return cursor.fetchall()

        profiles = make_request_to_db()
        profile_list = [
            {"id": profile[0], "email": profile[1], "username": profile[2], "currency": profile[3], "pvp_score": profile[4], "joindate": str(profile[5]), "role": profile[6]}
            for profile in profiles
        ]
        return jsonify(profile_list), 200

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ page_number +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ page_number +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ page_number +"]: Integrity error.")
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ page_number +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ page_number +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ page_number +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_history(get_user_history_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    get_user_history_request = GetUserHistoryRequest.from_dict(connexion.request.get_json())
    user_uuid = get_user_history_request.user_uuid
    history_type = get_user_history_request.history_type
    page_number = get_user_history_request.page_number

    mysql = current_app.extensions.get('mysql')


    try:
        not_found = False
        invalid_history_type = False

        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (user_uuid,))
            result = cursor.fetchone()
            if not result:
                return None, True, False  # history, not_found, invalid_history_type

            # user exists, continue
            offset = (page_number - 1) * 10 if page_number else 0

            if history_type == 'ingame':
                query = "SELECT BIN_TO_UUID(t.user_uuid) as user_uuid, t.credits, t.transaction_type, t.timestamp, p.username FROM ingame_transactions t JOIN profiles p ON t.user_uuid = p.uuid WHERE t.user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
            elif history_type == 'bundle':
                query = "SELECT BIN_TO_UUID(t.user_uuid) as user_uuid, t.bundle_codename, t.bundle_currency_name, t.timestamp, p.username FROM bundles_transactions t JOIN profiles p ON t.user_uuid = p.uuid WHERE t.user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
            else:
                return None, False, True  # history, not_found, invalid_history_type

            cursor.execute(query, (user_uuid, offset))
            history = cursor.fetchall()
            return history, False, False  # history, not_found, invalid_history_type


        history, not_found, invalid_history_type = make_request_to_db()

        if not_found:
            return "", 404

        if invalid_history_type:
            return "", 405

        if history_type == "ingame":
            history_list = [
                {"user_uuid": entry[0], "credits": entry[1], "transaction_type": entry[2], "timestamp": str(entry[3]), "username": entry[4]}
                for entry in history
            ]
        else:  # history_type == 'bundle'
            history_list = [
                {"user_uuid": entry[0], "codename": entry[1], "currency_name": entry[2], "timestamp": str(entry[3]), "username": entry[4]}
                for entry in history
            ]
        return jsonify(history_list), 200
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
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def update_auction(auction=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    auction = Auction.from_dict(connexion.request.get_json())


    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            no_auction_found = False
            no_item_found = False
            no_valid_bidder = False
            rows_updated = 0

            # check if auction with that uuid exists
            query = "SELECT uuid FROM auctions WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (auction.auction_uuid,))
            result = cursor.fetchone()
            if not result:
                no_auction_found = True

            # check if item with that uuid exists
            query = "SELECT item_uuid FROM inventories WHERE item_uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (auction.inventory_item_id,))
            result = cursor.fetchone()
            if not result:
                no_item_found = True

            # check if current bidder is a valid user uuid
            query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
            cursor.execute(query, (auction.current_bidder,))
            result = cursor.fetchone()
            if not result:
                no_valid_bidder = True
                

            # auction exists, continue
            query = "UPDATE auctions SET item_uuid = UUID_TO_BIN(%s), starting_price = %s, current_bid = %s, current_bidder = UUID_TO_BIN(%s), end_time = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (auction.inventory_item_id, auction.starting_price, auction.current_bid, auction.current_bidder, auction.end_time, auction.auction_uuid))
            connection.commit()
            rows_updated += cursor.rowcount
            
            return no_auction_found, no_item_found, no_valid_bidder, rows_updated

        no_auction_found, no_item_found, no_valid_bidder, rows_updated = make_request_to_db()

        if no_auction_found:
            return jsonify({"error": "Auction not found."}), 404
        
        if no_item_found:
            return jsonify({"error": "Item ID not found in any inventory."}), 404
        
        if no_valid_bidder:
            return jsonify({"error": "Current bidder user profile not found."}), 404

        if rows_updated == 0:
            return jsonify({"error": "Cannot update auction."}), 404

        return "", 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ auction.auction_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ auction.auction_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ auction.auction_uuid +"]: Integrity error.")
        return "", 409
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ auction.auction_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ auction.auction_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ auction.auction_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    return 'do some magic!'


def update_gacha(gacha=None): # TODO da fare
    """update_gacha

    Updates a specific gacha. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())
    return 'do some magic!'


def update_pool(pool=None): # TODO da fare
    """update_pool

    Updates a specific pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())
    return 'do some magic!'
