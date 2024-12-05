import json
import random
import uuid
from datetime import datetime

import connexion
import requests
from flask import current_app, jsonify, request, session
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server import util
from openapi_server.controllers.pvp_internal_controller import (
    delete_match,
    get_pending_list,
    get_status,
    insert_match,
    set_results,
    MOCK_PVPMATCHES
)
from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.input_checks import sanitize_team_input, sanitize_uuid_input
from openapi_server.helpers.logging import send_log
from openapi_server.helpers.stats import map_number_to_grade, map_grade_to_number
from openapi_server.models.pending_pv_p_requests import PendingPvPRequests
from openapi_server.models.pending_pv_p_requests_inner import PendingPvPRequestsInner
from openapi_server.models.pv_p_request import PvPRequest
from openapi_server.models.team import Team

circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

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

MOCK_INVENTORIES = {
    "f7e6d5c4-b3a2-9180-7654-321098fedcba": (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "2024-01-01",
        1,
        3000,
    ),
    "e6d5c4b3-a291-8076-5432-109876fedcba": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        3000,
    ),
    "d5c4b3a2-9180-7654-3210-9876fedcba98": (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        2500,
    ),
    "c7b6a5d4-e3f2-1098-7654-fedcba987654": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "2024-01-01",
        1,
        5000,
    ),
    "b7a6c5d4-e3f2-1098-7654-fedcba987655": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        5000,
    ),
    "a7b6c5d4-e3f2-1098-7654-fedcba987656": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        3000,
    ),
    "97b6c5d4-e3f2-1098-7654-fedcba987657": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7",
        "2024-01-04",
        1,
        3000,
    ),
    "87b6c5d4-e3f2-1098-7654-fedcba987658": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
        "2024-01-05",
        1,
        2000,
    ),
    "77b6c5d4-e3f2-1098-7654-fedcba987659": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
        "2024-01-06",
        1,
        1000,
    ),
    "67b6c5d4-e3f2-1098-7654-fedcba987660": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b",
        "2024-01-07",
        1,
        2000,
    ),
    "57b6c5d4-e3f2-1098-7654-fedcba987661": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
        "2024-01-08",
        1,
        5000,
    ),
    "47b6c5d4-e3f2-1098-7654-fedcba987662": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "2024-01-09",
        1,
        5000,
    ),
    "37b6c5d4-e3f2-1098-7654-fedcba987663": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
        "2024-01-10",
        1,
        3000,
    ),
    "27b6c5d4-e3f2-1098-7654-fedcba987664": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "e5f6a7b8-c9d0-1234-5678-90abcdef1234",
        "2024-01-11",
        1,
        3000,
    ),
    "17b6c5d4-e3f2-1098-7654-fedcba987665": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "f6a7b8c9-d0e1-2345-6789-0abcdef12345",
        "2024-01-12",
        1,
        2000,
    ),
    "07b6c5d4-e3f2-1098-7654-fedcba987666": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "c9d0e1f2-a3b4-5678-9012-cdef12345678",
        "2024-01-13",
        1,
        1000,
    ),
    "f6b6c5d4-e3f2-1098-7654-fedcba987667": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "a7b8c9d0-e1f2-3456-7890-abcdef123456",
        "2024-01-14",
        1,
        2000,
    ),
}

MOCK_GACHAS = {
    "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76": ("Star Platinum", "LEGENDARY", 5, 5, 5, 5, 3, 5, "2024-01-14"),
    "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632": ("The World", "LEGENDARY", 5, 5, 5, 5, 3, 5, "2024-01-14"),
    "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85": ("Gold Experience", "EPIC", 4, 4, 4, 4, 3, 5, "2024-01-14"),
    "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7": ("Crazy Diamond", "EPIC", 5, 5, 4, 5, 2, 4, "2024-01-14"),
    "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f": ("Silver Chariot", "RARE", 4, 5, 3, 5, 3, 3, "2024-01-14"),
    "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a": ("Hermit Purple", "COMMON", 2, 3, 3, 4, 4, 2, "2024-01-14"),
    "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b": ("Magicians Red", "RARE", 4, 3, 3, 3, 4, 3, "2024-01-14"),
    "f1a2b3c4-d5e6-f7a8-b9c0-1d2e3f4a5b6c": ("Hierophant Green", "RARE", 3, 3, 3, 5, 5, 3, "2024-01-14"),
    "a1b2c3d4-e5f6-7890-1234-567890abcdef": ("King Crimson", "LEGENDARY", 5, 4, 4, 4, 2, 5, "2024-01-14"),
    "b2c3d4e5-f6a7-8901-2345-67890abcdef1": ("Killer Queen", "EPIC", 4, 4, 4, 5, 3, 4, "2024-01-14"),
    "c3d4e5f6-a7b8-9012-3456-7890abcdef12": ("Made in Heaven", "LEGENDARY", 5, 5, 5, 5, 5, 5, "2024-01-14"),
    "d4e5f6a7-b8c9-0123-4567-890abcdef123": ("Sticky Fingers", "RARE", 4, 4, 3, 4, 2, 3, "2024-01-14"),
    "e5f6a7b8-c9d0-1234-5678-90abcdef1234": ("Purple Haze", "EPIC", 5, 3, 3, 2, 2, 2, "2024-01-14"),
    "f6a7b8c9-d0e1-2345-6789-0abcdef12345": ("Sex Pistols", "RARE", 2, 3, 4, 5, 5, 2, "2024-01-14"),
    "a7b8c9d0-e1f2-3456-7890-abcdef123456": ("Aerosmith", "RARE", 3, 4, 3, 4, 5, 2, "2024-01-14"),
    "b8c9d0e1-f2a3-4567-8901-bcdef1234567": ("Moody Blues", "RARE", 2, 3, 3, 5, 2, 3, "2024-01-14"),
    "c9d0e1f2-a3b4-5678-9012-cdef12345678": ("Beach Boy", "COMMON", 1, 2, 3, 5, 5, 2, "2024-01-14"),
    "d0e1f2a3-b4c5-6789-0123-def123456789": ("White Album", "RARE", 3, 3, 5, 3, 2, 3, "2024-01-14"),
    "e1f2a3b4-c5d6-7890-1234-ef123456789a": ("Stone Free", "EPIC", 4, 4, 4, 5, 3, 4, "2024-01-14"),
    "f2a3b4c5-d6e7-8901-2345-f123456789ab": ("Weather Report", "EPIC", 4, 3, 4, 4, 4, 5, "2024-01-14"),
    "a3b4c5d6-e7f8-9012-3456-123456789abc": ("D4C", "LEGENDARY", 5, 4, 5, 4, 3, 5, "2024-01-14"),
    "b4c5d6e7-f8a9-0123-4567-23456789abcd": ("Tusk Act 4", "LEGENDARY", 5, 3, 5, 4, 3, 5, "2024-01-14"),
    "c5d6e7f8-a9b0-1234-5678-3456789abcde": ("Soft & Wet", "EPIC", 4, 4, 4, 5, 2, 5, "2024-01-14"),
}

SERVICE_TYPE = "pvp"


def pvp_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def accept_pvp_request(pvp_match_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error": "Invalid input"}), 400
    
    response = get_status(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    match_data = response[0].get_json()

    sender_uuid = match_data["sender_id"]
    receiver_uuid = match_data["receiver_id"]

    if receiver_uuid != session["uuid"]:
        return jsonify({"error": "This request is not for you"}), 401

    if match_data["winner_id"] == "":
        winner = None
    elif match_data["winner_id"] == match_data["sender_id"]:
        winner = True
    else:
        winner = False

    if winner is not None:
        return jsonify({"error": "Match already ended"}), 406

    if not connexion.request.is_json:
        return jsonify({"error": "Invalid request."}), 400

    player2_team = connexion.request.get_json()

    player2_team = sanitize_team_input(player2_team)
    if not player2_team:
        return jsonify({"error": "Invalid input"}), 400

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            global MOCK_INVENTORIES
            
            team_uuids = player2_team
            # Check if all items in the team belong to the user
            for item_uuid in team_uuids:
                if item_uuid not in MOCK_INVENTORIES or MOCK_INVENTORIES[item_uuid][0] != session["uuid"]:
                    return False, 404

            return True, 200

        ownership_verified, status_code = make_request_to_inventory_service()

        if not ownership_verified:
            if status_code == 404:
                return jsonify({"error": "Items not found in user inventory."}), 404

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    player1_team = match_data["teams"]["team1"]

    random.shuffle(player2_team)

    stats = ["stat_power", "stat_speed", "stat_durability", "stat_precision", "stat_range"]
    points = 0
    log = {"rounds": []}

    for i in range(7):
        extracted_stat = random.choice(stats)

        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                global MOCK_INVENTORIES
                item_data = MOCK_INVENTORIES.get(player1_team[i])
                if not item_data:
                    return None, 404
                return item_data[1], 200       

            response_data, status_code = make_request_to_inventory_service()
            if status_code == 404:
                return "", 404

            player1_stand = response_data

            @circuit_breaker
            def make_request_to_inventory_service():
                global MOCK_INVENTORIES
                item_data = MOCK_INVENTORIES.get(player1_team[i])
                if not item_data:
                    return None, 404
                return item_data[1], 200       

            response_data, status_code = make_request_to_inventory_service()
            if status_code == 404:
                return "", 404
            
            player2_stand = response_data

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "Items not found in user inventory."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:
            @circuit_breaker
            def make_request_to_gacha_service():
                global MOCK_GACHAS
                
                gacha_data = MOCK_GACHAS.get(player1_stand) 
                
                if not gacha_data:
                    return {"error": "Gacha not found"}, 404
                
                name, rarity, power, speed, durability, precision, range_, potential, release_date = (
                    gacha_data 
                )

                # Construct the Gacha object for the response
                gacha_obj = {
                    "gacha_uuid": player1_stand,
                    "name": name,
                    "rarity": rarity,
                    "attributes": {
                        "power": map_number_to_grade(power),  
                        "speed": map_number_to_grade(speed),
                        "durability": map_number_to_grade(durability),
                        "precision": map_number_to_grade(precision),
                        "range": map_number_to_grade(range_),
                        "potential": map_number_to_grade(potential),
                    },
                }
                
                return gacha_obj, 200

            player1_stand_data, status_code = make_request_to_gacha_service()
            
            if status_code == 404:
                return jsonify({"error": "Gacha not found."}), 404

            @circuit_breaker
            def make_request_to_gacha_service():
                global MOCK_GACHAS

                gacha_data = MOCK_GACHAS.get(player2_stand) 

                if not gacha_data:
                    return {"error": "Gacha not found"}, 404

                name, rarity, power, speed, durability, precision, range_, potential, release_date = (
                    gacha_data  # Unpack tuple
                )

                # Construct the Gacha object for the response
                gacha_obj = {
                    "gacha_uuid": player2_stand,
                    "name": name,
                    "rarity": rarity,
                    "attributes": {
                        "power": map_number_to_grade(power),  
                        "speed": map_number_to_grade(speed),
                        "durability": map_number_to_grade(durability),
                        "precision": map_number_to_grade(precision),
                        "range": map_number_to_grade(range_),
                        "potential": map_number_to_grade(potential),
                    },
                }

                return gacha_obj, 200

            player2_stand_data , status_code = make_request_to_gacha_service()
            if status_code == 404:
                return jsonify({"error": "Gacha not found."}), 404

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return jsonify({"error": "Gacha not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        player1_stand_name = player1_stand_data["name"]
        player2_stand_name = player2_stand_data["name"]
        player1_stand_potential = player1_stand_data["attributes"]["potential"]
        player2_stand_potential = player2_stand_data["attributes"]["potential"]
        player1_stand_stat = map_grade_to_number(player1_stand_data["attributes"][extracted_stat.replace("stat_", "")])
        player2_stand_stat = map_grade_to_number(player2_stand_data["attributes"][extracted_stat.replace("stat_", "")])
        if player1_stand_stat > player2_stand_stat:
            points += 1
            round_winner = "Player 1"
            winner_name = player1_stand_name
        elif player1_stand_stat < player2_stand_stat:
            points -= 1
            round_winner = "Player 2"
            winner_name = player2_stand_name
        else:
            if player1_stand_potential > player2_stand_potential:
                points += 1
                round_winner = "Player 1"
                winner_name = player1_stand_name
            elif player1_stand_potential < player2_stand_potential:
                points -= 1
                round_winner = "Player 2"
                winner_name = player2_stand_name
            else:
                random_choice = random.choice([1, -1])
                points += random_choice
                if random_choice > 0:
                    round_winner = "Player 1"
                    winner_name = player1_stand_name
                else:
                    round_winner = "Player 2"
                    winner_name = player2_stand_name
        
        log["rounds"].append(
            {
                "extracted_stat": extracted_stat.replace("stat_", ""),
                "player1": {"stand_name": player1_stand_name, "stand_stat": map_number_to_grade(player1_stand_stat)},
                "player2": {"stand_name": player2_stand_name, "stand_stat": map_number_to_grade(player2_stand_stat)},
                "round_winner": round_winner+"'s "+winner_name,
            }
        )
    
    if points > 0:
        winner = True
        winner_id = sender_uuid
    else:
        winner = False
        winner_id = receiver_uuid
    
    try:

        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": session["uuid"], "points_to_add": abs(points)}
            url = "https://service_profile/profile/internal/add_pvp_score"
            response = requests.post(
                url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
            )
            response.raise_for_status()

        make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


    log_json = json.dumps(log)

    payload = {
        "pvp_match_uuid": pvp_match_uuid,
        "sender_id": sender_uuid,
        "receiver_id": receiver_uuid,
        "teams": {"team1": player1_team, "team2": player2_team},
        "winner_id": winner_id,
        "match_log": log_json,
        "match_timestamp": datetime.now(),
    }
    
    response = set_results(payload, None)

    if response[1] == 200:
        return response
    else:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def check_pending_pvp_requests():
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    response = get_pending_list(None, session["uuid"])

    if response[1] == 200:
        return response
    else:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def get_pvp_status(pvp_match_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error": "Invalid input"}), 400

    response = get_status(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] == 200:
        return response
    else:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def reject_pv_prequest(pvp_match_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error": "Invalid input"}), 400
    
    response = get_status(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] != 200:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    match_data = response[0].get_json()
    if match_data["receiver_id"] != session['uuid']:
        return jsonify({"error": "Cannot reject this match."}), 403
    
    if match_data["winner_id"] != "":
        return jsonify({"error": "Match already disputed."}), 403

    response = delete_match(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] == 200:
        return jsonify({"message": "Match rejected successfully."}), 200
    else:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def send_pvp_request(user_uuid):
    response = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if response[1] != 200:
        return response
    else:
        session = response[0]
    #### END AUTH CHECK

    valid, user_uuid = sanitize_uuid_input(user_uuid)
    if not valid:
        return jsonify({"error": "Invalid input"}), 400

    if session["uuid"] == user_uuid:
        return jsonify({"error": "You cannot start a match with yourself."}), 406

    if not connexion.request.is_json:
        return jsonify({"error": "Invalid request."}), 400

    team = connexion.request.get_json()

    team = sanitize_team_input(team)
    if not team:
        return jsonify({"error": "Invalid input"}), 400

    try:

        @circuit_breaker
        def make_request_to_profile_service():
            global MOCK_PROFILES
            if user_uuid not in MOCK_PROFILES:
                result = None
            else:
                result = MOCK_PROFILES[user_uuid]
            return {"exists": result is not None}

        exist_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if exist_data["exists"] == False:
        return jsonify({"error": "User not found."}), 404

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            global MOCK_INVENTORIES
            
            team_uuids = team
            # Check if all items in the team belong to the user
            for item_uuid in team_uuids:
                if item_uuid not in MOCK_INVENTORIES or MOCK_INVENTORIES[item_uuid][0] != session["uuid"]:
                    return False, 404

            return True, 200

        ownership_verified, status_code = make_request_to_inventory_service()

        if not ownership_verified:
            if status_code == 404:
                return jsonify({"error": "Items not found in user inventory."}), 404

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    match_uuid = str(uuid.uuid4())
    payload = {
        "pvp_match_uuid": match_uuid,
        "sender_id": session["uuid"],
        "receiver_id": user_uuid,
        "teams": {"team1": team, "team2": ["", "", "", "", "", "", ""]},
        "winner_id": "",
        "match_log": {},
        "match_timestamp": datetime.now()
    }

    response = insert_match(payload, None)

    if response[1] != 201:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    return jsonify({"message": "Match request sent successfully."}), 200
