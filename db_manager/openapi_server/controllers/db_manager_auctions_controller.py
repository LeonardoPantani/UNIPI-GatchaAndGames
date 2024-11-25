import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest
from openapi_server.models.complete_auction_sale_request import CompleteAuctionSaleRequest
from openapi_server.models.get_auction_status200_response import GetAuctionStatus200Response
from openapi_server.models.get_auction_status_request import GetAuctionStatusRequest
from openapi_server.models.get_item_with_owner200_response import GetItemWithOwner200Response
from openapi_server.models.get_item_with_owner_request import GetItemWithOwnerRequest
from openapi_server.models.get_user_currency200_response import GetUserCurrency200Response
from openapi_server.models.get_user_involved_auctions_request import GetUserInvolvedAuctionsRequest
from openapi_server.models.list_auctions_request import ListAuctionsRequest
from openapi_server.models.place_bid_request import PlaceBidRequest
from openapi_server import util

from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError
import logging
from datetime import datetime


# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def complete_auction_sale(complete_auction_sale_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    complete_auction_sale_request = CompleteAuctionSaleRequest.from_dict(connexion.request.get_json())
    
    item_uuid = complete_auction_sale_request.item_uuid
    current_bid = complete_auction_sale_request.current_bid
    bidder_uuid = complete_auction_sale_request.user_uuid

    mysql = current_app.extensions.get('mysql')
    connection = None

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT BIN_TO_UUID(owner_uuid) FROM inventories WHERE item_uuid = UUID_TO_BIN(%s)',
                (item_uuid,)
            )
            old_owner_uuid = cursor.fetchone()[0]
            print("After select")
            cursor.execute(
                'UPDATE profiles SET currency = currency + %s WHERE uuid = UUID_TO_BIN(%s)',
                (current_bid, old_owner_uuid)
            )
            print("after update")
            cursor.execute(
                'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, "sold_market")',
                (old_owner_uuid,current_bid)
            )
            print("after insert")
            cursor.execute(
                'UPDATE inventories SET owner_uuid = UUID_TO_BIN(%s) WHERE item_uuid = UUID_TO_BIN(%s)',
                (bidder_uuid, item_uuid)
            )
            print(bidder_uuid)
            print(current_bid*(-1))
            cursor.execute(
                'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, "bought_market")',
                (bidder_uuid, current_bid*(-1))
            )
            
            return
        
        make_request_to_db()

        return "", 200
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ bidder_uuid + ", " + item_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def create_auction(get_auction_status200_response=None):

    if not connexion.request.is_json:
        return "", 400
    
    #wrong names are still openapi's fault
    request = GetAuctionStatus200Response.from_dict(connexion.request.get_json())
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

            result = cursor.fetchone()
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
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ auction_uuid + ", " + item_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_auction_status(get_auction_status_request=None):
    
    if not connexion.request.is_json:
        return "", 400    
    
    get_auction_status_request = GetAuctionStatusRequest.from_dict(connexion.request.get_json())

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
            return "", 404
        
        status = "closed" if datetime.now() > auction[6] else "open"

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
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ auction_uuid +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ auction_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ auction_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ auction_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_item_with_owner(get_item_with_owner_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_item_with_owner_request = GetItemWithOwnerRequest.from_dict(connexion.request.get_json())

    user_uuid = get_item_with_owner_request.user_uuid
    item_uuid = get_item_with_owner_request.item_uuid

    mysql = current_app.extensions.get('mysql')
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
            return "", 404

        payload = {
            "owner_id": item[0],
            "item_id": item[1],
            "gacha_uuid": item[2],
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
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ item_uuid +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ item_uuid +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ item_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ item_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ item_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_user_currency(ban_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    #wrong name is openapi's fault
    user_currency_request = BanUserProfileRequest.from_dict(connexion.request.get_json())
    
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
            return "", 404

        payload = {
            "currency": currency[0]
        }

        return payload, 200
    
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid +"]: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid +"]: Data error.")
        return "", 500
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


def get_user_involved_auctions(get_user_involved_auctions_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_user_involved_auctions_request = GetUserInvolvedAuctionsRequest.from_dict(connexion.request.get_json())

    user_uuid = get_user_involved_auctions_request.user_uuid
    page_number = get_user_involved_auctions_request.page_number

    items_per_page = 10
    offset = (page_number-1)*10

    mysql = current_app.extensions.get('mysql')
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.execute( 
                'SELECT BIN_TO_UUID(a.uuid), BIN_TO_UUID(a.item_uuid), BIN_TO_UUID(i.owner_uuid), a.starting_price, a.current_bid, BIN_TO_UUID(a.current_bidder), end_time FROM auctions a JOIN inventories i ON a.item_uuid = i.item_uuid WHERE i.owner_uuid = UUID_TO_BIN(%s) OR a.current_bidder = UUID_TO_BIN(%s) LIMIT %s OFFSET %s',
                (user_uuid, user_uuid, items_per_page, offset)
            )
            return cursor.fetchall()
        
        auction_list = make_request_to_db()

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    
    if not auction_list:
        return "", 404
    
    # Prepare the response data
    auctions = []
    now = datetime.now()
    for auction in auction_list:
        auction_uuid, item_id, owner_id, starting_price, current_bid, current_bidder, end_time = auction
        
        # Determine auction status based on the end time
        status = "closed" if end_time < now else "open"
        
        auctions.append({
            "auction_uuid": auction_uuid,
            "inventory_item_id": item_id,
            "inventory_item_owner_id": owner_id,
            "starting_price": starting_price,
            "current_bid": current_bid,
            "current_bidder": current_bidder, #if this is the user it's an auction he has bid on, otherwise the user is the owner of the item or the auction hasn't been claimed yet
            "end_time": end_time,
            "status": status
        })

    return jsonify(auctions), 200


def list_auctions(list_auctions_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    list_auctions_request = ListAuctionsRequest.from_dict(connexion.request.get_json())
    
    status = list_auctions_request.status
    rarity = list_auctions_request.rarity
    page_number = list_auctions_request.page_number

    items_per_page = 10
    offset = (page_number-1)*10
    now = datetime.now()

    mysql = current_app.extensions.get('mysql')

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()

            query = '''
                SELECT BIN_TO_UUID(a.uuid) AS auction_id, a.end_time
                FROM auctions a
                JOIN inventories i ON a.item_uuid = i.item_uuid
                JOIN gachas_types g ON i.stand_uuid = g.uuid
                WHERE a.end_time {}
                '''.format('< %s' if status == 'closed' else '> %s')

            # Parameters for the query
            params = [now]

            if rarity:
                query += 'AND g.rarity = %s '
                params.append(rarity)

            query += 'LIMIT %s OFFSET %s'
            params.extend([items_per_page, offset])

            # Execute the query
            cursor.execute(query, tuple(params))

            auction_data = cursor.fetchall()
            
            return auction_data
        
        auction_list = make_request_to_db()
        
        if not auction_list: # rimuovere 404, restituire lista vuota
            return "", 404
        
        auctions = []
        for auction in auction_list:
            auction_uuid, end_time = auction
            # Determine the auction status
            status = "closed" if end_time < now else "open"

            auctions.append({"auction_uuid": auction_uuid})
        
        return jsonify(auctions), 200

    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query: Programming error.")
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def place_bid(place_bid_request=None):
    if not connexion.request.is_json:
        return "", 400
        
    place_bid_request = PlaceBidRequest.from_dict(connexion.request.get_json())

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
        return "", 500
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Data error.")
        return "", 500
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid + ", " + auction_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503