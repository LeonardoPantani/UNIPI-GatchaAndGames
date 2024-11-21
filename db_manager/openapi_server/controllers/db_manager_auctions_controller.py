import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest  # noqa: E501
from openapi_server.models.complete_auction_sale_request import CompleteAuctionSaleRequest  # noqa: E501
from openapi_server.models.get_auction_status200_response import GetAuctionStatus200Response  # noqa: E501
from openapi_server.models.get_auction_status_request import GetAuctionStatusRequest  # noqa: E501
from openapi_server.models.get_item_with_owner200_response import GetItemWithOwner200Response  # noqa: E501
from openapi_server.models.get_item_with_owner_request import GetItemWithOwnerRequest  # noqa: E501
from openapi_server.models.get_user_currency200_response import GetUserCurrency200Response  # noqa: E501
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest  # noqa: E501
from openapi_server.models.list_auctions_request import ListAuctionsRequest  # noqa: E501
from openapi_server.models.place_bid_request import PlaceBidRequest  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging
from datetime import datetime


# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def complete_auction_sale(complete_auction_sale_request=None):  # noqa: E501
    """complete_auction_sale

    Completes the sale of an auctioned item by transferring ownership, updating balances, and logging transactions for the buyer and the seller. # noqa: E501

    :param complete_auction_sale_request: 
    :type complete_auction_sale_request: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        complete_auction_sale_request = CompleteAuctionSaleRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def create_auction(get_auction_status200_response=None):  # noqa: E501

    if not connexion.request.is_json:
        return "", 400
    
    #wrong names are still openapi's fault
    request = GetAuctionStatus200Response.from_dict(connexion.request.get_json())  # noqa: E501
    auction_request = request.auction
    auction_uuid = auction_request.auction_uuid
    item_uuid = auction_request.inventory_item_id
    starting_price = auction_request.starting_price
    end_time = auction_request.end_time

    mysql = current_app.extensions.get('mysql')
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT BIN_TO_UUID(uuid) FROM auctions WHERE item_uuid = UUID_TO_BIN(%s) AND end_time > %s',
                (item_uuid, datetime.now())
            )

            result = cursor.fetchone()[0]
            if result:
                return "", 409

            cursor.execute(
                'INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, 0, NULL, %s)',
                (auction_uuid, item_uuid, starting_price, end_time)
            )
            connection.commit()
            return "", 201
        
        _ , code = make_request_to_db()

        return "", code
    
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_auction_status(get_auction_status_request=None):  # noqa: E501
    
    if not connexion.request.is_json:
        return "", 400    
    
    get_auction_status_request = GetAuctionStatusRequest.from_dict(connexion.request.get_json())  # noqa: E501

    auction_uuid = get_auction_status_request.uuid

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            #Get auction status from database
            cursor.execute(
                "SELECT BIN_TO_UUID(a.uuid), BIN_TO_UUID(i.owner_uuid), BIN_TO_UUID(a.item_uuid), starting_price, current_bid, BIN_TO_UUID(a.current_bidder), end_time FROM auctions a JOIN inventories i ON a.item_uuid = i.item_uuid WHERE a.uuid = UUID_TO_BIN(%s)",
                (auction_uuid,)
            )
            return cursor.fetchone()
        
        auction = make_request_to_db()

        if not auction:
                return jsonify({"error": "Auction not found for given UUID."}), 404
        
        status = "closed" if datetime.now() > auction[6] else "active"

        payload = {
            "auction_uuid": auction_uuid,
            "status": status,
            "inventory_item_owner_id": auction[1],
            "inventory_item_id": auction[2],
            "starting_price": auction[3],
            "current_bid": auction[4],
            "current_bidder": auction[5],
            "end_time": auction[6]
        }

        return payload, 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ auction_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ auction_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ auction_uuid +"]: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ auction_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ auction_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ auction_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ auction_uuid +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503

def get_item_with_owner(get_item_with_owner_request=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    get_item_with_owner_request = GetItemWithOwnerRequest.from_dict(connexion.request.get_json())  # noqa: E501

    user_uuid = get_item_with_owner_request.user_uuid
    item_uuid = get_item_with_owner_request.item_uuid

    mysql = current_app.extensions.get('mysql')
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT BIN_TO_UUID(owner_uuid), BIN_TO_UUID(item_uuid), BIN_TO_UUID(stand_uuid), obtained_at, owners_no, currency_spent FROM inventories WHERE BIN_TO_UUID(owner_uuid) = %s AND BIN_TO_UUID(item_uuid) = %s',
                (user_uuid, item_uuid)
            )
            return cursor.fetchone()
        
        item = make_request_to_db()
        
        if not item:
            return jsonify({"error":"Item not found in user's inventory."}), 404

        payload = {
            "owner_id": item[0],
            "item_id": item[1],
            "gacha_uuid": item[2],
            "pull_date": None, #forse si aggiunge
            "obtained_date": item[3].strftime("%Y-%m-%d %H:%M:%S"),
            "owners_no": item[4],
            "price_paid": item[5]
        }
        
        return jsonify(payload), 200
    
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ item_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ item_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ item_uuid +"]: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ item_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ item_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ item_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ item_uuid +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_currency(ban_user_profile_request=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    #wrong name is openapi's fault
    user_currency_request = BanUserProfileRequest.from_dict(connexion.request.get_json())  # noqa: E501
    
    user_uuid = user_currency_request.user_uuid

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            #Get user's currency from the database
            cursor.execute(
                'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
                (user_uuid,)
            )
            return cursor.fetchone()
        
        currency = make_request_to_db()

        if not currency:
            return jsonify({"error": "User not found for the given UUID."}), 404

        payload = {
            "currency": currency[0]
        }

        return payload, 200
    
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid +"]: Integrity error.")
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_involved_auctions(get_user_involved_auctions_request=None):  # noqa: E501
    """get_user_involved_auctions

    Gets a list of all auctions the user is involved in, either as a seller or as a bidder, with pagination. # noqa: E501

    :param get_user_involved_auctions_request: 
    :type get_user_involved_auctions_request: dict | bytes

    :rtype: Union[List[Auction], Tuple[List[Auction], int], Tuple[List[Auction], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        get_user_involved_auctions_request = GetUserInvolvedAuctionsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def list_auctions(list_auctions_request=None):  # noqa: E501
    """list_auctions

    Returns a list of all auctions, filtered by status, rarity, and supports pagination. # noqa: E501

    :param list_auctions_request: 
    :type list_auctions_request: dict | bytes

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        list_auctions_request = ListAuctionsRequest.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def place_bid(place_bid_request=None):  # noqa: E501

    if not connexion.request.is_json:
        return "", 400
        
    place_bid_request = PlaceBidRequest.from_dict(connexion.request.get_json())  # noqa: E501

    user_uuid = place_bid_request._user_uuid
    auction_uuid = place_bid_request.auction_uuid
    new_bid = place_bid_request.new_bid

    mysql = current_app.extensions.get('mysql')
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            # Updates auction bid details in the database
            cursor.execute(
                'SELECT BIN_TO_UUID(current_bidder), current_bid FROM auctions WHERE uuid = UUID_TO_BIN(%s)',
                (auction_uuid,)
            )
            previous_bidder, previous_bid = cursor.fetchone()
            
            cursor.execute( 
                'UPDATE auctions SET current_bid = %s, current_bidder = UUID_TO_BIN(%s) WHERE uuid = UUID_TO_BIN(%s)',
                (new_bid, user_uuid, auction_uuid)
            )
            #updates user funds
            cursor.execute(
                'UPDATE profiles SET currency = currency - %s WHERE uuid = UUID_TO_BIN(%s)',
                (new_bid, user_uuid)
            )
            #gives old bidder his funds back
            if previous_bidder is not None:
                cursor.execute(
                    'UPDATE profiles SET currency = currency + %s WHERE BIN_TO_UUID(uuid) = %s',
                    (previous_bid, previous_bidder)
                )
            connection.commit()
            return
        
        make_request_to_db()

        return "", 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503