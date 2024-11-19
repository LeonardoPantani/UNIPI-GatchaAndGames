import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server import util

from flask import jsonify, request, session, current_app
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import uuid
from datetime import datetime, timedelta
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
auction_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

@auction_circuit_breaker
def bid_on_auction(auction_uuid): 
    #check if user is logged in
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    user_uuid = session['uuid']
    #get args
    increment = request.args.get('bid', type=int)
    
    if increment < 1:
        return jsonify({"error": "Invalid bid value."}), 400

    try:
        #connect to database
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()
        #get auction from database
        cursor.execute( #/db_manager/auctions/get_auction_status
            'SELECT item_uuid, starting_price, current_bid, current_bidder, end_time FROM auctions WHERE BIN_TO_UUID(uuid) = %s',
            (auction_uuid,)
        )

        auction = cursor.fetchone()

        if not auction:
            return jsonify({"error": "Auction not found."}), 404
        
        item_uuid, starting_price, current_bid, current_bidder, end_time = auction
        
        #prepare new data to insert
        if not current_bid:
            new_bid = starting_price
        else:    
            new_bid = current_bid + increment

        if datetime.now() > end_time:
            return jsonify({"error":"Auction is closed"}), 403

        cursor.execute( #/db_manager/auctions/get_item_with_owner
            'SELECT * FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s) AND item_uuid = %s',
            (user_uuid, item_uuid)
        )

        item_found = cursor.fetchone()
        if item_found:
            return jsonify({"error":"Cannot bid on your own auctions"}), 400
        
        if user_uuid == current_bidder:
            return jsonify({"message":"Already the highest bidder"}), 200

        cursor.execute( #/db_manager/auctions/get_currency
            'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
            (user_uuid,)
        )
        user_profile = cursor.fetchone()
        
        if not user_profile:
            return jsonify({"error": "User profile not found."}), 404
        #check if user has enough funds
        user_currency = user_profile[0]
        if user_currency < new_bid:
            return jsonify({"error": "Insufficient funds."}), 406
        #updates auction
        cursor.execute( #/db_manager/auctions/place_bid
            'UPDATE auctions SET current_bid = %s, current_bidder = UUID_TO_BIN(%s) WHERE uuid = %s',
            (new_bid, user_uuid, auction_uuid)
        )
        #updates user funds
        cursor.execute(
            'UPDATE profiles SET currency = currency - %s WHERE uuid = UUID_TO_BIN(%s)',
            (new_bid, user_uuid)
        )
        #gives old bidder his funds back
        if current_bidder is not None:
            cursor.execute( #/db_manager/auctions/refund_previous_bidder
                'UPDATE profiles SET currency = currency + %s WHERE BIN_TO_UUID(uuid) = %s',
                (current_bid, current_bidder)
            )
        
        connection.commit()

        return jsonify({"message": "Bid placed successfully."}), 200

    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Rollback transaction on error
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Close the database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@auction_circuit_breaker
def create_auction(): 

    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403 

    starting_price = request.args.get('starting_price', default=10, type=int)

    if starting_price < 1:
        return jsonify({"error": "Invalid query parameters."}), 400

    owner_id = request.args.get('inventory_item_owner_id')
    item_id = request.args.get('inventory_item_id')

    if not owner_id or not item_id:
        return jsonify({"error": "Invalid query parameters."}), 400
        
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute( #/db_manager/auctions/get_item_with_owner (si prendono poi solo i dati necessari per non creare ulteriori endpoint)
            'SELECT owner_uuid FROM inventories WHERE BIN_TO_UUID(owner_uuid) = %s AND BIN_TO_UUID(item_uuid) = %s',
            (owner_id, item_id)
        )

        searched_item = cursor.fetchone()
        if not searched_item:
            return jsonify({"error": "Item not found in player's inventory."}), 404
        
        auction_id = uuid.uuid4()
        end_time = datetime.now() + timedelta(minutes=10)

        cursor.execute( #/db_manager/auctions/create
            'INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s, %s, %s)',
            (auction_id, item_id, starting_price, None, None, end_time)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message":"Auction created successfully."}), 200
    
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Rollback transaction on error
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Close the database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@auction_circuit_breaker
def get_auction_status(auction_uuid): 
    
    if 'username' not in session:
        return jsonify({"error":"Not logged in"}), 403
    
    try:

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error":"Database not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute( #/db_manager/auctions/get_auction_status
            "SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time FROM auctions WHERE uuid = UUID_TO_BIN(%s)",
            (auction_uuid,)
        )

        auction_data = cursor.fetchone()

        if not auction_data:
            return jsonify({"error": "Auction not found"}), 404
    
        ( _ , item_uuid, starting_price, current_bid, current_bidder, end_time) = auction_data

        status = "closed" if datetime.now() > end_time else "active"

        response = {
            "auction_uuid": auction_uuid,
            "inventory_item_id": item_uuid,
            "starting_price": starting_price,
            "current_bid": current_bid,
            "current_bidder": current_bidder,
            "end_time": end_time,
            "status": status
        }
        
        if status == 'closed':
            username = session['username']

            cursor.execute(
                'SELECT owner_uuid FROM inventories WHERE item_uuid = UUID_TO_BIN(%s)',
                (item_uuid,)
            )
            old_owner_uuid = cursor.fetchone()[0]

            cursor.execute(
                'SELECT BIN_TO_UUID(uuid) FROM profiles WHERE username = %s',
                (username,)
            )

            user_uuid = cursor.fetchone()[0] #extracts only the string from the tuple returned by fetchone
            if not user_uuid:
                return jsonify({"error": "User not found"}), 404
            
            if current_bidder == user_uuid:
                cursor.execute(
                    'UPDATE profiles SET currency = currency + %s WHERE uuid = %s',
                    (current_bid, old_owner_uuid)
                )
                cursor.execute(
                    'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, "sold_market")',
                    (old_owner_uuid,current_bid)
                )
                cursor.execute(
                    'UPDATE inventories SET owner_uuid = UUID_TO_BIN(%s) WHERE item_uuid = UUID_TO_BIN(%s)',
                    (user_uuid, item_uuid)
                )
                cursor.execute(
                    'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, "bought_market")',
                    (user_uuid,current_bid*(-1))
                )
            #not removed from auctions for history
                full_response = {**response, "message": "Item redeemed successfully"}
                return jsonify(full_response), 200

        return jsonify(response), 200

    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Handle errors and rollback if any database operation failed
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        # Close the database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@auction_circuit_breaker
def get_auctions_history(page_number=None):  
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    user_uuid=session['uuid']
    
    page_number = int(request.args.get('page_number', 1))

    items_per_page = 10
    offset = (page_number - 1) * items_per_page

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:

        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute( #/db_manager/auctions/get_user_involved_auctions
            'SELECT BIN_TO_UUID(a.uuid), BIN_TO_UUID(a.item_uuid), a.starting_price, a.current_bid, BIN_TO_UUID(a.current_bidder), end_time FROM auctions a JOIN inventories i ON a.item_uuid = i.item_uuid WHERE i.owner_uuid = %s OR a.current_bidder = %s LIMIT %s OFFSET %s',
            (user_uuid, user_uuid, items_per_page, offset)
        )

        auction_data = cursor.fetchall()

        if not auction_data:
            return jsonify({"error": "No auctions found"}), 404
        
        # Prepare the response data
        auctions = []
        now = datetime.now()
        for auction in auction_data:
            auction_uuid, item_id, starting_price, current_bid, current_bidder, end_time = auction
            
            # Determine auction status based on the end time
            status = "closed" if end_time < now else "active"
            
            auctions.append({
                "auction_uuid": auction_uuid,
                "inventory_item_id": item_id,
                "starting_price": starting_price,
                "current_bid": current_bid,
                "current_bidder": current_bidder, #if this is the user it's an auction he has bid on, otherwise the user is the owner of the item or the auction hasn't been claimed yet
                "end_time": end_time,
                "status": status
            })

        return jsonify(auctions), 200

    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Handle database connection errors or any exceptions
        return jsonify({"error": str(e)}), 500

    finally:
        # Close database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@auction_circuit_breaker
def get_auctions_list(status=None, rarity=None, page_number=None): 
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    status = request.args.get('status','active')
    rarity = request.args.get('rarity')
    page_number = int(request.args.get('page_number',1))

    items_per_page = 10
    offset = (page_number - 1) * items_per_page

    now = datetime.now()

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:

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

        if not auction_data:
            return jsonify({"error": "No auctions found"}), 404
        
        auctions = []
        for auction in auction_data:
            auction_uuid, end_time = auction
            # Determine the auction status
            status = "closed" if end_time < now else "active"

            auctions.append({
                "auction_uuid": auction_uuid,
                "status": status,
                "end_time": end_time
            })

        return jsonify(auctions), 200
    
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Handle database connection errors or any exceptions
        return jsonify({"error": str(e)}), 500

    finally:
        # Close database connection
        cursor.close()
        connection.close()