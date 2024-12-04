############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import logging
from datetime import datetime, date


import connexion
import requests
from flask import jsonify, current_app
from mysql.connector.errors import (
    DatabaseError,
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.models.auction import Auction
from openapi_server.models.auction_status import AuctionStatus
from openapi_server.models.gacha_rarity import GachaRarity

SERVICE_TYPE="auction"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)

MOCK_AUCTIONS = {
    "aabbccdd-eeff-0011-2233-445566778899": (
        "aabbccdd-eeff-0011-2233-445566778899",
        "f7e6d5c4-b3a2-9180-7654-321098fedcba",
        5000,
        6000,
        "87f3b5d1-5e8e-4fa4-909b-3cd29c4b1f09",
        "2025-02-01 00:00:00"
    ),
    "a9b8c7d6-e5f4-3210-9876-fedcba987654": (
        "a9b8c7d6-e5f4-3210-9876-fedcba987654",
        "c7b6a5d4-e3f2-1098-7654-fedcba987654",
        5000,
        6500,
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "2025-02-01 00:00:00"
    ),
}

MOCK_INVENTORIES = {
    "f7e6d5c4-b3a2-9180-7654-321098fedcba": (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "2024-01-01",
        1,
        3000,
    ),
    "e6d5c4b3-a291-4807-8765-43210987fedc": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        3000,
    ),
    "d5c4b3a2-9180-4765-4321-09876fedcba9": (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        2500,
    ),
    "c7b6a5d4-e3f2-1098-7654-fedcba987654": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "2024-01-01",
        1,
        5000,
    ),
    "b7a6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        5000,
    ),
    "a7b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        3000,
    ),
    "97b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7",
        "2024-01-04",
        1,
        3000,
    ),
    "87b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
        "2024-01-05",
        1,
        2000,
    ),
    "77b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "d4e5f6a7-b8c9-4d1e-2f3a-4b5c6d7e8f9a",
        "2024-01-06",
        1,
        1000,
    ),
    "67b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b",
        "2024-01-07",
        1,
        2000,
    ),
    "57b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "c3d4e5f6-a7b8-4012-3456-7890abcdef12",
        "2024-01-08",
        1,
        5000,
    ),
    "47b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "2024-01-09",
        1,
        5000,
    ),
    "37b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "b2c3d4e5-f6a7-4901-2345-67890abcdef1",
        "2024-01-10",
        1,
        3000,
    ),
    "27b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "e5f6a7b8-c9d0-4234-5678-90abcdef1234",
        "2024-01-11",
        1,
        3000,
    ),
    "17b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "f6a7b8c9-d0e1-4234-5678-90abcdef1234",
        "2024-01-12",
        1,
        2000,
    ),
    "07b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "c9d0e1f2-a3b4-5678-9012-cdef12345678",
        "2024-01-13",
        1,
        1000,
    ),
    "f6b6c5d4-e3f2-4109-8765-4fedcba98765": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "a7b8c9d0-e1f2-3456-7890-abcdef123456",
        "2024-01-14",
        1,
        2000,
    ),
}

MOCK_GACHAS = {
    '1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76': ('Star Platinum', 'LEGENDARY', 5, 5, 5, 5, 3, 5, "2024-01-14"),
    '9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632': ('The World', 'LEGENDARY', 5, 5, 5, 5, 3, 5, "2024-01-14"),
    'b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85': ('Gold Experience', 'EPIC', 4, 4, 4, 4, 3, 5, "2024-01-14"),
    '8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7': ('Crazy Diamond', 'EPIC', 5, 5, 4, 5, 2, 4, "2024-01-14"),
    'c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f': ('Silver Chariot', 'RARE', 4, 5, 3, 5, 3, 3, "2024-01-14"),
    'd4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a': ('Hermit Purple', 'COMMON', 2, 3, 3, 4, 4, 2, "2024-01-14"),
    'e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b': ('Magicians Red', 'RARE', 4, 3, 3, 3, 4, 3, "2024-01-14"),
    'f1a2b3c4-d5e6-f7a8-b9c0-1d2e3f4a5b6c': ('Hierophant Green', 'RARE', 3, 3, 3, 5, 5, 3, "2024-01-14"),
    'a1b2c3d4-e5f6-7890-1234-567890abcdef': ('King Crimson', 'LEGENDARY', 5, 4, 4, 4, 2, 5, "2024-01-14"),
    'b2c3d4e5-f6a7-8901-2345-67890abcdef1': ('Killer Queen', 'EPIC', 4, 4, 4, 5, 3, 4, "2024-01-14"),
    'c3d4e5f6-a7b8-9012-3456-7890abcdef12': ('Made in Heaven', 'LEGENDARY', 5, 5, 5, 5, 5, 5, "2024-01-14"),
    'd4e5f6a7-b8c9-0123-4567-890abcdef123': ('Sticky Fingers', 'RARE', 4, 4, 3, 4, 2, 3, "2024-01-14"),
    'e5f6a7b8-c9d0-1234-5678-90abcdef1234': ('Purple Haze', 'EPIC', 5, 3, 3, 2, 2, 2, "2024-01-14"),
    'f6a7b8c9-d0e1-2345-6789-0abcdef12345': ('Sex Pistols', 'RARE', 2, 3, 4, 5, 5, 2, "2024-01-14"),
    'a7b8c9d0-e1f2-3456-7890-abcdef123456': ('Aerosmith', 'RARE', 3, 4, 3, 4, 5, 2, "2024-01-14"),
    'b8c9d0e1-f2a3-4567-8901-bcdef1234567': ('Moody Blues', 'RARE', 2, 3, 3, 5, 2, 3, "2024-01-14"),
    'c9d0e1f2-a3b4-5678-9012-cdef12345678': ('Beach Boy', 'COMMON', 1, 2, 3, 5, 5, 2, "2024-01-14"),
    'd0e1f2a3-b4c5-6789-0123-def123456789': ('White Album', 'RARE', 3, 3, 5, 3, 2, 3, "2024-01-14"),
    'e1f2a3b4-c5d6-7890-1234-ef123456789a': ('Stone Free', 'EPIC', 4, 4, 4, 5, 3, 4, "2024-01-14"),
    'f2a3b4c5-d6e7-8901-2345-f123456789ab': ('Weather Report', 'EPIC', 4, 3, 4, 4, 4, 5, "2024-01-14"),
    'a3b4c5d6-e7f8-9012-3456-123456789abc': ('D4C', 'LEGENDARY', 5, 4, 5, 4, 3, 5, "2024-01-14"),
    'b4c5d6e7-f8a9-0123-4567-23456789abcd': ('Tusk Act 4', 'LEGENDARY', 5, 3, 5, 4, 3, 5,"2024-01-14"),
    'c5d6e7f8-a9b0-1234-5678-3456789abcde': ('Soft & Wet', 'EPIC', 4, 4, 4, 5, 2, 5, "2024-01-14"),
}

MOCK_PROFILES = {
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": (
        "JotaroKujo",
        5000,
        100,
        "2024-01-05 10:00:00",
    ),
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": (
        "DIOBrando",
        16000,
        95,
        "2024-01-05 11:00:00",
    ),
    "a4f0c592-12af-4bde-aacd-94cd0f27c57e": (
        "GiornoGiovanna",
        4500,
        85,
        "2024-01-05 12:00:00",
    ),
    "b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d": (
        "JosukeHigashikata",
        3500,
        80,
        "2024-01-05 13:00:00",
    ),
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284": (
        "SpeedwagonAdmin",
        10000,
        98,
        "2024-01-05 14:00:00",
    ),
    "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6": (
        "AdminUser",
        100000000,
        999,
        "2024-01-05 15:00:00",
    ),
}

def create_auction(auction = None, session=None):
    if not auction:
        if not connexion.request.is_json:
            return "", 400
            
        auction = Auction.from_dict(connexion.request.get_json())

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
            global MOCK_AUCTIONS

            MOCK_AUCTIONS[uuid] = (
                uuid,
                item_id,
                starting_price,
                0,
                None,
                end_time
            )

        insert_auction()

        return jsonify({"message":"Auction created."}), 201

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def exists_auctions(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def search_auction():
            global MOCK_AUCTIONS
            if uuid not in MOCK_AUCTIONS:
                result = None
            else:
                result = MOCK_AUCTIONS[uuid]
            return result is not None

        auction = search_auction()

        exists = False
        if auction: 
            exists = True

        payload = {
            "exists": exists
        }

        return jsonify(payload), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def get_auction(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def search_auction():
            global MOCK_AUCTIONS
            result = MOCK_AUCTIONS.get(uuid)

            return result

        auction = search_auction()

        if not auction:
            return "", 404
        
        @circuit_breaker
        def make_request_to_inventory_service():
            global MOCK_INVENTORIES

            item_uuid = auction[1]
            
            result = MOCK_INVENTORIES.get(item_uuid)

            return result
        
        item = make_request_to_inventory_service()
        if not item:
            return "", 404
        
        owner_uuid = item[1]

        status = "open" if datetime.strptime(auction[5], "%Y-%m-%d %H:%M:%S") > datetime.now() else "closed"

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

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def get_auction_list(session=None, status=None, rarity=None, page_number=None):
    if connexion.request.is_json:
        status =  AuctionStatus.from_dict(connexion.request.get_json())
    if connexion.request.is_json:
        rarity =  GachaRarity.from_dict(connexion.request.get_json())
    
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
            global MOCK_AUCTIONS

            if status == "open":
                filtered_auctions = {
                    k: v for k, v in MOCK_AUCTIONS.items() if datetime.strptime(v[5], "%Y-%m-%d %H:%M:%S") > datetime.now()
                }
            else:
                filtered_auctions = {
                    k: v for k, v in MOCK_AUCTIONS.items() if datetime.strptime(v[5], "%Y-%m-%d %H:%M:%S") < datetime.now()
                }

            return filtered_auctions

        auction_list = get_auction_list()

        response = []
        keep = True
        for auction in auction_list.items():
            try:
                @circuit_breaker
                def make_request_to_inventory_service():
                    global MOCK_INVENTORIES

                    return MOCK_INVENTORIES.get(auction[1][1])
                
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

            if not item:
                return "", 404
            if rarity:
                try:
                    @circuit_breaker
                    def make_request_to_gacha_service():
                        global MOCK_GACHAS

                        rarity = MOCK_GACHAS.get(item[1])[1]

                        return {"rarity": rarity}
                    
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
                owner_uuid = item[0]
                
                status = "open" if datetime.strptime(auction[1][5], "%Y-%m-%d %H:%M:%S") > datetime.now() else "closed"

                payload = {
                    "auction_uuid": auction[0],
                    "status": status,
                    "inventory_item_owner_id": owner_uuid,
                    "inventory_item_id": auction[1][1],
                    "starting_price": auction[1][2],
                    "current_bid": auction[1][3],
                    "current_bidder": auction[1][4],
                    "end_time": auction[1][5]
                } 
                response.append(payload)
            keep = True

        return jsonify(response[offset:(offset+items_per_page)]), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def get_user_auctions(session=None, user_uuid=None):
    if not user_uuid:
        return "", 400

    try:
        @circuit_breaker
        def make_request_to_inventory_service():
            global MOCK_INVENTORIES

            filtered_items = []
            for k, v in MOCK_INVENTORIES.items():
                if v[0] == user_uuid:
                    filtered_items.append(k)

            return filtered_items
        
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
    print(item_list)
    try:
        @circuit_breaker
        def get_user_auctions():
            global MOCK_AUCTIONS

            filtered_auctions = []
            for k, v in MOCK_AUCTIONS.items():
                if v[1] in item_list or v[4] == user_uuid:
                    filtered_auctions.append(v)

            return filtered_auctions
        
        auction_list = get_user_auctions()

        response = []
        for auction in auction_list:
            status = "open" if datetime.strptime(auction[5], "%Y-%m-%d %H:%M:%S") > datetime.now() else "closed"
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

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def is_open_by_item_uuid(session=None, uuid=None):
    if not uuid:
        return "", 400
    print(uuid)
    try:
        @circuit_breaker
        def search_auction():
            global MOCK_AUCTIONS
            result = MOCK_AUCTIONS.get(uuid)

            return result
        
        auction_data = search_auction()
        print(auction_data)
        if not auction_data or datetime.strptime(auction_data[5], "%Y-%m-%d %H:%M:%S") < datetime.now():
            return jsonify({"found":False}), 200

        return jsonify({"found":True}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def refund_bidders(request_body=None, session=None):
    request_body = connexion.request.get_json()

    if request_body == []:
        return "", 200

    if not request_body:
        return "", 400
    
    try:
        @circuit_breaker
        def get_auctions():
            global MOCK_AUCTIONS

            filtered_auctions = []
            for k, v in MOCK_AUCTIONS.items():
                if v[1] in request_body and datetime.strptime(v[5], "%Y-%m-%d %H:%M:%S") > datetime.now():
                    filtered_auctions.append(v)

            return filtered_auctions
        
        auction_list = get_auctions()

        for auction in auction_list:
            if auction[4] is not None:
                try:
                    @circuit_breaker
                    def make_request_to_profile_service():
                        global MOCK_PROFILES

                        if auction[4] not in MOCK_PROFILES:
                            return 404
                        
                        MOCK_PROFILES[auction[4]] = (
                            MOCK_PROFILES[auction[4]][0],
                            MOCK_PROFILES[auction[4]][1] + auction[3],
                            MOCK_PROFILES[auction[4]][2],
                            MOCK_PROFILES[auction[4]][3],
                        )
                        return 200
                    
                    code = make_request_to_profile_service()
                    
                except requests.HTTPError as e:
                    if e.response.status_code == 404: 
                        return jsonify({"error": "User not found."}), 404
                    else:
                        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
                except requests.RequestException:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
                except CircuitBreakerError:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  
                if code == 404:
                    return jsonify({"error": "User not found."}), 404
                elif code != 200:
                    return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        return jsonify({"message":"Bidders refunded."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def remove_by_item_uuid(request_body=None, session=None):
    request_body = connexion.request.get_json()

    if request_body == []:
        return "", 200

    if not request_body:
        return "", 400

    
    try:
        @circuit_breaker
        def delete_auctions():
            global MOCK_AUCTIONS

            MOCK_AUCTIONS = {
                k: v for k, v in MOCK_AUCTIONS.items() if v[1] not in request_body
            }

        delete_auctions()
        print(MOCK_AUCTIONS)
        return jsonify({"message":"Auctions deleted."}), 200
        
    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def reset_current_bidder(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def update_auction():
            global MOCK_AUCTIONS
            updated = False

            for k,v in MOCK_AUCTIONS.items():
                if v[4] == uuid:

                    v_list = list(v)
                    v_list[3] = 0
                    v_list[4] = None

                    MOCK_AUCTIONS[k] = tuple(v_list)

                    updated = True

            if not updated:
                return 304
            
            return 200
        
        status_code = update_auction()
        
        if status_code == 304:
            return jsonify({"message":"No changes applied."}), 304

        return jsonify({"message":"Bid updated."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def set_bid(session=None, auction_uuid=None, user_uuid=None, new_bid=None):
    if not auction_uuid or not user_uuid or not new_bid:
        return "", 400

    try:
        @circuit_breaker
        def update_auction():
            global MOCK_AUCTIONS

            if auction_uuid not in MOCK_AUCTIONS:
                return 404
            else:
                auction = MOCK_AUCTIONS[auction_uuid]

            if datetime.strptime(auction[5], "%Y-%m-%d %H:%M:%S") < datetime.now():
                return 403
            
            auction_list = list(auction)

            auction_list[3] = new_bid
            auction_list[4] = user_uuid

            MOCK_AUCTIONS[auction_uuid] = tuple(auction_list)

            return 200

        status_code = update_auction()

        if status_code == 404:
            return jsonify({"error":"Auction not found."}), 404
        
        if status_code == 403:
            return jsonify({"error":"Auction not open."}), 403

        return jsonify({"message":"Bid updated."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503


def update_auction(session=None, auction=None):
    if not connexion.request.is_json:
        return "", 400
        
    auction = Auction.from_dict(connexion.request.get_json())

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
            if uuid not in MOCK_AUCTIONS:
                return 404
            
            auction = MOCK_AUCTIONS[uuid]

            auction_list = list(auction)

            updated = False

            if item_id is not None:
                auction_list[1] = item_id
                updated = True

            if starting_price is not None:
                auction_list[2] = starting_price
                updated = True

            if current_bid is not None:
                auction_list[3] = current_bid
                updated = True

            if current_bidder is not None:
                auction_list[4] = current_bidder
                updated = True

            if end_time is not None:
                auction_list[5] = end_time
                updated = True

            if not updated:
                return 304

            MOCK_AUCTIONS[uuid] = tuple(auction_list)

            return 200

        
        status_code = update_auction()
        
        if status_code == 404:
            return jsonify({"error":"Auction not found."}), 404
        
        if status_code == 304:
            return jsonify({"message":"No changes applied."}), 304

        return jsonify({"message":"Auction updated."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        return "", 503