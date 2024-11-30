import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from pybreaker import CircuitBreaker, CircuitBreakerError
from flask import jsonify, session
import requests
import logging
from datetime import datetime

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.auction_status import AuctionStatus  # noqa: E501
from openapi_server.models.exists_auctions200_response import ExistsAuctions200Response  # noqa: E501
from openapi_server.models.gacha_rarity import GachaRarity  # noqa: E501
from openapi_server.models.is_open_by_item_uuid200_response import IsOpenByItemUuid200Response  # noqa: E501
from openapi_server import util

from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

def create_auction(auction = None, session=None):  # noqa: E501
    if not auction:
        if not connexion.request.is_json:
            return "", 400
            
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501

        uuid = auction.auction_uuid
        item_id = auction.inventory_item_id
        starting_price = auction.starting_price
        end_time = auction.end_time
    else:
        uuid = auction.get("auction_uuid")
        item_id = auction.get("inventory_item_id")
        starting_price = auction.get("starting_price")
        end_time = auction.get("end_time")

    if not uuid or not item_id or not starting_price or not end_time:
        return "", 400

    try:
        @circuit_breaker
        def insert_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                INSERT INTO auctions
                (uuid, item_uuid, starting_price, current_bid, current_bidder, end_time)
                VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s, NULL, %s)
            """

            cursor.execute(query, (uuid, item_id, starting_price, 0, end_time))

            connection.commit()

            cursor.close()

        insert_auction()

        return jsonify({"message":"Auction created."}), 201

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError as e:
        logging.error(f"Query: Programming error.{e}")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError as e:
        logging.error(f"Query: Generic database error.{e}")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_auctions(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def search_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT *
                FROM auctions
                WHERE uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            result = cursor.fetchone()

            cursor.close()

            return result

        auction = search_auction()

        exists = False
        if auction: 
            exists = True

        payload = {
            "exists": exists
        }

        return jsonify(payload), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_auction(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def search_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                FROM auctions
                WHERE uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            result = cursor.fetchone()

            cursor.close()

            return result

        auction = search_auction()

        if not auction:
            return "", 404
        
        try:
            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": auction[1]}
                url = "https://service_inventory/inventory/internal/get_by_item_uuid"
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response.json()
            
            item = make_request_to_inventory_service()
        except requests.HTTPError as e:
            if e.response.status_code == 404: 
                return jsonify({"error": "Item not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  
        
        owner_uuid = item["owner_id"]

        status = "open" if auction[5] > datetime.now() else "closed"

        payload = {
            "auction_uuid": auction[0],
            "status": status,
            "inventory_item_owner_id": owner_uuid,
            "inventory_item_id": auction[1],
            "starting_price": auction[2],
            "current_bid": auction[3],
            "current_bidder": auction[4],
            "end_time": auction[5]
        }

        return jsonify(payload), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_auction_list(session=None, status=None, rarity=None, page_number=None):  # noqa: E501
    if connexion.request.is_json:
        status =  AuctionStatus.from_dict(connexion.request.get_json())  # noqa: E501
    if connexion.request.is_json:
        rarity =  GachaRarity.from_dict(connexion.request.get_json())  # noqa: E501
    
    if not status or (status != "open" and status != "closed"):
        return "", 400
    
    if rarity and (rarity != "common" and rarity != "rare" and rarity != "epic" and rarity != "legendary"):
        return "", 400

    items_per_page = 10
    offset = (page_number - 1) * items_per_page 

    if rarity:
        rarity=rarity.upper()

    try:
        @circuit_breaker
        def get_auction_list():
            connection = get_db()
            cursor = connection.cursor()

            if status == "open":
                query = """
                    SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                    FROM auctions
                    WHERE end_time > %s
                """
            else:
                query = """
                    SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                    FROM auctions
                    WHERE end_time < %s 
                """

            cursor.execute(query, (datetime.now(),))

            result = cursor.fetchall()

            cursor.close()

            return result

        auction_list = get_auction_list()

        response = []
        keep = True
        for auction in auction_list:
            try:
                @circuit_breaker
                def make_request_to_inventory_service():
                    params = {"uuid": auction[1]}
                    url = "https://service_inventory/inventory/internal/get_by_item_uuid"
                    response = requests.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
                
                item = make_request_to_inventory_service()
            except requests.HTTPError as e:
                if e.response.status_code == 404: # user not found, hiding as 401
                    return jsonify({"error": "Item not found."}), 404
                else:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
            except requests.RequestException:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
            except CircuitBreakerError:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503 

            if rarity:
                try:
                    @circuit_breaker
                    def make_request_to_gacha_service():
                        params = {"uuid": item["gacha_uuid"]}
                        url = "https://service_gacha/gacha/internal/get_rarity_by_uuid"
                        response = requests.get(url, params=params)
                        response.raise_for_status()
                        return response.json()
                    
                    obtained_rarity = make_request_to_gacha_service()
                except requests.HTTPError as e:
                    if e.response.status_code == 404: # user not found, hiding as 401
                        return jsonify({"error": "Item not found."}), 404
                    else:
                        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
                except requests.RequestException:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
                except CircuitBreakerError:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

                if not obtained_rarity:
                    return "", 404
                
                if rarity != obtained_rarity["rarity"]:
                    keep = False

            if keep:
                owner_uuid = item["owner_id"]

                status = "open" if auction[5] > datetime.now() else "closed"

                payload = {
                    "auction_uuid": auction[0],
                    "status": status,
                    "inventory_item_owner_id": owner_uuid,
                    "inventory_item_id": auction[1],
                    "starting_price": auction[2],
                    "current_bid": auction[3],
                    "current_bidder": auction[4],
                    "end_time": auction[5]
                } 
                response.append(payload)
            keep = True

        return jsonify(response[offset:(offset+items_per_page)]), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_user_auctions(session=None, user_uuid=None):  # noqa: E501
    if not user_uuid:
        return "", 400

    try:
        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"uuid": user_uuid}
            url = "https://service_inventory/inventory/internal/get_items_by_owner_uuid"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        item_list = make_request_to_inventory_service()
    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

    try:
        @circuit_breaker
        def get_user_auctions():
            connection = get_db()
            cursor = connection.cursor()

            if item_list:
                query = """
                    SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                    FROM auctions
                    WHERE item_uuid IN ({})
                    OR current_bidder = %s
                """.format(','.join(['UUID_TO_BIN(%s)'] * len(item_list)))
                params = item_list + [user_uuid]
            else:
                query = """
                    SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                    FROM auctions
                    WHERE current_bidder = %s
                """
                params = [user_uuid]

            cursor.execute(query, params)
            auctions_data = cursor.fetchall()

            cursor.close()

            return auctions_data
        
        auction_list = get_user_auctions()

        response = []
        for auction in auction_list:
            status = "open" if auction[5] > datetime.now() else "closed"
            payload = {
                "auction_uuid": auction[0],
                "status": status,
                "inventory_item_owner_id": user_uuid,
                "inventory_item_id": auction[1],
                "starting_price": auction[2],
                "current_bid": auction[3],
                "current_bidder": auction[4],
                "end_time": auction[5]
            }
            response.append(payload)
        
        return jsonify(response), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def is_open_by_item_uuid(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    print(uuid)
    try:
        @circuit_breaker
        def search_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                FROM auctions
                WHERE item_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            result = cursor.fetchone()

            cursor.close()

            return result
        
        auction_data = search_auction()
        print(auction_data)
        if not auction_data or auction_data[5] < datetime.now():
            return jsonify({"found":False}), 200

        return jsonify({"found":True}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def refund_bidders(request_body=None, session=None):  # noqa: E501
    request_body = connexion.request.get_json()

    if not request_body:
        return "", 400
    
    if request_body == []:
        return "", 200
    
    try:
        @circuit_breaker
        def get_auctions():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(uuid), BIN_TO_UUID(item_uuid), starting_price, current_bid, BIN_TO_UUID(current_bidder), end_time
                FROM auctions
                WHERE item_uuid IN ({})
                AND end_time > %s
            """.format(','.join(['UUID_TO_BIN(%s)'] * len(request_body)))
            params = request_body + [datetime.now()]

            cursor.execute(query, params)
            auctions_data = cursor.fetchall()

            cursor.close()

            return auctions_data
        
        auction_list = get_auctions()
        
        for auction in auction_list:
            if auction[4] is not None:
                try:
                    @circuit_breaker
                    def make_request_to_profile_service():
                        params = {"uuid": auction[4], "amount": auction[3]}
                        url = "https://service_profile/profile/internal/add_currency"
                        response = requests.post(url, params=params)
                        response.raise_for_status()
                        return response.json()
                    
                    make_request_to_profile_service()
                except requests.HTTPError as e:
                    print(e)
                    if e.response.status_code == 404: 
                        return jsonify({"error": "User not found."}), 404
                    else:
                        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
                except requests.RequestException:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
                except CircuitBreakerError:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

        return jsonify({"message":"Bidders refunded."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def remove_by_item_uuid(request_body=None, session=None):  # noqa: E501
    request_body = connexion.request.get_json()

    if not request_body:
        return "", 400
    
    if request_body == []:
        return "", 200
    
    try:
        @circuit_breaker
        def delete_auctions():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                DELETE
                FROM auctions
                WHERE item_uuid IN ({})
            """.format(','.join(['UUID_TO_BIN(%s)'] * len(request_body)))

            cursor.execute(query, request_body)

            connection.commit()
            cursor.close()

        delete_auctions()

        return jsonify({"message":"Auctions deleted."}), 200
        
    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def reset_current_bidder(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def update_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                UPDATE auctions
                SET current_bid = 0, current_bidder= NULL
                WHERE current_bidder = UUID_TO_BIN(%s)              
            """

            cursor.execute(query, (uuid,))
            if cursor.rowcount == 0:
                return 304
            connection.commit()

            cursor.close()

            return 200

        status_code = update_auction()

        if status_code == 304:
            return jsonify({"message":"No changes applied."}), 304

        return jsonify({"message":"Bid updated."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def set_bid(session=None, auction_uuid=None, user_uuid=None, new_bid=None):  # noqa: E501
    if not auction_uuid or not user_uuid or not new_bid:
        return "", 400

    try:
        @circuit_breaker
        def update_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT *
                FROM auctions
                WHERE uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (auction_uuid,))
            cursor.fetchone()
            if cursor.rowcount == 0:
                return 404

            query = """
                UPDATE auctions
                SET current_bid = %s, current_bidder = UUID_TO_BIN(%s)
                WHERE uuid = UUID_TO_BIN(%s)
                AND end_time > %s              
            """

            cursor.execute(query, (new_bid, user_uuid, auction_uuid, datetime.now()))
            if cursor.rowcount == 0:
                return 403
            
            connection.commit()

            cursor.close()

            return 200

        status_code = update_auction()

        if status_code == 404:
            return jsonify({"error":"Auction not found."}), 404
        
        if status_code == 403:
            return jsonify({"error":"Auction not open."}), 403

        return jsonify({"message":"Bid updated."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError:
        logging.error(f"Query: Programming error.")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def update_auction(session=None, auction=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
        
    auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501

    uuid = auction.auction_uuid
    item_id = auction.inventory_item_id
    starting_price = auction.starting_price
    current_bid = auction.current_bid
    current_bidder = auction.current_bidder
    end_time = auction.end_time

    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def update_auction():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT *
                FROM auctions
                WHERE uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))
            cursor.fetchone()
            if cursor.rowcount == 0:
                return 404

            query = "UPDATE auctions SET "
            params = []
            updates = []

            # Append columns that need to be updated
            if item_id is not None:
                updates.append("item_uuid = UUID_TO_BIN(%s)")
                params.append(item_id)

            if starting_price is not None:
                updates.append("starting_price = %s")
                params.append(starting_price)

            if current_bid is not None:
                updates.append("current_bid = %s")
                params.append(current_bid)

            if current_bidder is not None:
                updates.append("current_bidder = UUID_TO_BIN(%s)")
                params.append(current_bidder)

            if end_time is not None:
                updates.append("end_time = %s")
                params.append(end_time)

            # Ensure there is something to update
            if not updates:
                return 304

            # Join the update parts and complete the query
            query += ", ".join(updates)
            query += " WHERE uuid = UUID_TO_BIN(%s)"
            params.append(uuid)

            # Execute the query with the parameters
            cursor.execute(query, params)
            if cursor.rowcount == 0:
                return 304

            connection.commit()

            cursor.close()

        status_code = update_auction()

        if status_code == 404:
            return jsonify({"error":"Auction not found."}), 404
        
        if status_code == 304:
            return jsonify({"message":"No changes applied."}), 304

        return jsonify({"message":"Auction updated."}), 200

    except OperationalError:
        logging.error(f"Query: Operational error.")
        return "", 503
    except ProgrammingError as e:
        logging.error(f"Query: Programming error.{e}")
        return "", 503
    except DataError:
        logging.error(f"Query: Invalid data error.")
        return "", 503 
    except IntegrityError:
        logging.error(f"Query: Integrity error.")
        return "", 503
    except DatabaseError as e:
        logging.error(f"Query: Generic database error.{e}")
        return "", 503
    except CircuitBreakerError:
        return "", 503