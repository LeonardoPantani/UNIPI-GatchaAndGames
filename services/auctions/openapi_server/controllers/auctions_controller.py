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

def bid_on_auction(auction_uuid):  # noqa: E501
    """Bids on an active auction

    Sends a bid to an active auction, if the user has enough currency. # noqa: E501

    :param session: 
    :type session: str
    :param auction_uuid: Id of the auction to bid on.
    :type auction_uuid: str
    :type auction_uuid: str
    :param bid: Bid value.
    :type bid: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    #if 'username' not in session:
    #    return jsonify({"error": "Not logged in"}), 403 #se non va cambiare a 400 per rispettare specs

    increment = request.args.get('bid', type=int)
    auction_uuid = request.args.get('auction_id')

    if increment < 1:
        return jsonify({"error": "Invalid bid value."}), 400

    try:

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT current_bid, current_bidder, end_time FROM auctions WHERE uuid = %s',
            (auction_uuid)
        )

        auction = cursor.fetchone()

        if not auction:
            return jsonify({"error": "Auction not found."}), 404
        
        current_bid, current_bidder, end_time = auction

        new_bid = current_bid + increment

        if datetime.now() > end_time:
            return jsonify({"error":"Auction is closed"}), 403
        
        user_uuid = session['username']

        cursor.execute(
            'SELECT currency FROM profiles WHERE uuid = %s',
            (user_uuid)
        )

        user_profile = cursor.fetchone()

        if not user_profile:
            return jsonify({"error": "User profile not found."}), 404
        
        user_currency = user_profile[0]
        if user_currency < new_bid:
            return jsonify({"error": "Insufficient funds."}), 406
        
        cursor.execute(
            'UPDATE auctions SET current_bid = %s, current_bidder = %s WHERE uuid = %s',
            (new_bid, user_uuid, auction_uuid)
        )

        cursor.execute(
            'UPDATE profiles SET currency = currency - %s WHERE uuid = %s',
            (new_bid, user_uuid)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message": "Bid placed successfully."}), 200

    except Exception as e:
        # Rollback transaction on error
        connection.rollback()
        return jsonify({"error": str(e)}), 500

    return 'do some magic!'


def create_auction():  # noqa: E501  NOT WORKING
    """Creates an auction.

    Creates an auction for an item in player&#39;s inventory. # noqa: E501

    :param session: 
    :type session: str
    :param gacha_item: The item to sell in the auction.
    :type gacha_item: dict | bytes
    :param starting_price: The starting price of the auction.
    :type starting_price: int

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    try:
        if not isinstance(gacha_item, dict) or 'gacha_item' not in gacha_item:
            return jsonify({"error":"invalid gacha_item format"}), 400

        owner_id = gacha_item.get("owner_id")
        item_id = gacha_item.get("item_id")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403 #se non va cambiare a 400 per rispettare specs

    starting_price = request.args.get('starting_price', default=10, type=int)

    if starting_price < 1:
        return jsonify({"error": "Invalid query parameters."}), 400
    
    #if connexion.request.is_json:
    #    gacha_item =  InventoryItemId.from_dict(connexion.request.get_json()) 
     #   owner_id = gacha_item.get("owner_id")
      #  item_id = gacha_item.get("item_id")

    #if connexion.request.is_json:
     #   gacha_item = connexion.request.get_json()
      #  owner_id = gacha_item.get("owner_id")
       # item_id = gacha_item.get("item_id")
    #else:
    # Handle case where parameters are passed in query string
     #   owner_id = request.args.get('owner_id')
      #  item_id = request.args.get('item_id')

    if not owner_id or not item_id:
        return jsonify({"error": "Invalid query parameters."}), 400
        
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT owner_uuid FROM inventories WHERE owner_uuid = %s AND item_uuid = %s',
            (owner_id, item_id)
        )

        searched_item = cursor.fetchone()
        if not searched_item:
            return jsonify({"error": "Item in player's inventory not found."}), 404
        
        auction_id = uuid.uuid4().bytes
        end_time = datetime.now() + timedelta(minutes=10)

        cursor.execute(
            'INSERT INTO auctions (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time) VALUES (%s, %s, %s, %s, %s)',
            (auction_id, item_id, starting_price, None, None, end_time)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return jsonify({"message":"Auction created successfully."}), 200
    
    except Exception as e:
        # Rollback transaction on error
        connection.rollback()
        return jsonify({"error": str(e)}), 500

    #return jsonify({"error": "Invalid request."}), 400


def get_auction_status(session, auction_uuid):  # noqa: E501
    """Retrieve info on specific auction.

    Returns info on the auction with a specific id. # noqa: E501

    :param session: 
    :type session: str
    :param auction_uuid: The id of the auction to obtain info
    :type auction_uuid: str
    :type auction_uuid: str

    :rtype: Union[Auction, Tuple[Auction, int], Tuple[Auction, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auctions_history(session, page_number=None):  # noqa: E501
    """Retrieve history of my auctions.

    Returns a list of all my auctions for gacha items. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_auctions_list(status=None, rarity=None, page_number=None):  # noqa: E501
    """Retrieve the list of auctions.

    Returns a list of all active auctions for gacha items. # noqa: E501

    :param session: 
    :type session: str
    :param status: Filter auctions by status.
    :type status: str
    :param rarity: Filter auctions by type of gacha item.
    :type rarity: dict | bytes
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    if connexion.request.is_json:
        rarity =  GachaRarity.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
