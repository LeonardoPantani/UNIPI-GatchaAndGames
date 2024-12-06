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
            params = {"user_uuid": session["uuid"]}
            payload = {"team": player2_team}
            url = "https://service_inventory/inventory/internal/check_owner_of_team"
            response = requests.post(
                url, params=params, json=payload, verify=False, timeout=current_app.config["requests_timeout"]
            )
            response.raise_for_status()

        make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"make_request_to_inventory_service: Some items not found in user {session['username']} inventory", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            send_log(f"make_request_to_inventory_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_inventory_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_inventory_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    player1_team = json.loads(match_data["teams"])["team1"]

    random.shuffle(player2_team)

    stats = ["stat_power", "stat_speed", "stat_durability", "stat_precision", "stat_range"]
    points = 0
    log = {"rounds": []}

    for i in range(7):
        extracted_stat = random.choice(stats)

        try:

            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": player1_team[i]}
                url = "https://service_inventory/inventory/internal/get_stand_uuid_by_item_uuid"
                response = requests.get(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            response_data = make_request_to_inventory_service()

            player1_stand = response_data["stand_uuid"]

            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": player2_team[i]}
                url = "https://service_inventory/inventory/internal/get_stand_uuid_by_item_uuid"
                response = requests.get(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            response_data = make_request_to_inventory_service()

            player2_stand = response_data["stand_uuid"]

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                send_log("make_request_to_inventory_service: Some items not found in user's inventory", level="info", service_type=SERVICE_TYPE)
                return jsonify({"error": "Items not found in user inventory."}), 404
            else:
                send_log(f"make_request_to_inventory_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException as e:
            send_log(f"make_request_to_inventory_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            send_log(f"make_request_to_inventory_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        try:
            
            @circuit_breaker
            def make_request_to_gacha_service():
                params = {"uuid": player1_stand}
                url = "https://service_gacha/gacha/internal/gacha/get"
                response = requests.get(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )

                response.raise_for_status()
                return response.json()

            player1_stand_data = make_request_to_gacha_service()

            @circuit_breaker
            def make_request_to_gacha_service():
                params = {"uuid": player2_stand}
                url = "https://service_gacha/gacha/internal/gacha/get"
                response = requests.get(
                    url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
                )
                response.raise_for_status()
                return response.json()

            player2_stand_data = make_request_to_gacha_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                send_log("make_request_to_gacha_service: Gacha not found", level="info", service_type=SERVICE_TYPE)
                return jsonify({"error": "Gacha not found."}), 404
            else:
                send_log(f"make_request_to_gacha_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
                return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
        except requests.RequestException as e:
            send_log(f"make_request_to_gacha_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            send_log(f"make_request_to_gacha_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
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
            params = {"uuid": winner_id, "points_to_add": abs(points)}
            url = "https://service_profile/profile/internal/add_pvp_score"
            response = requests.post(
                url, params=params, verify=False, timeout=current_app.config["requests_timeout"]
            )
            response.raise_for_status()

        make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"make_request_to_profile_service: No user found with uuid: {winner_id}", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "User not found."}), 404
        else:
            send_log(f"make_request_to_profile_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_profile_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_profile_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
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
        send_log(f"accept_pvp_request: User {session['username']} has successfully accepted and performed match {pvp_match_uuid}.", level="general", service_type=SERVICE_TYPE)
        return response
    else:
        send_log(f"set_results: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
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
        send_log(f"check_pending_pvp_requests: User {session['username']} has successfully gotten its pending match requests.", level="general", service_type=SERVICE_TYPE)
        return response
    else:
        send_log(f"get_pending_list: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
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
        send_log(f"get_status: No match found with uuid: {pvp_match_uuid} by user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return response
    elif response[1] == 200:
        send_log(f"get_pvp_status: User {session['username']} has successfully gotten match {pvp_match_uuid} info.", level="general", service_type=SERVICE_TYPE)
        return response
    else:
        send_log(f"get_status: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
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
        send_log(f"get_status: No match found with uuid: {pvp_match_uuid} by user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return response
    elif response[1] != 200:
        send_log(f"get_status: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    match_data = response[0].get_json()
    if match_data["receiver_id"] != session['uuid']:
        send_log(f"reject_pv_prequest: User {session['username']} tried to reject match with uuid: {pvp_match_uuid} but it wasn't for him.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Cannot reject this match."}), 403
    
    if match_data["winner_id"] != "":
        send_log(f"reject_pv_prequest: User {session['username']} tried to reject match with uuid: {pvp_match_uuid} but it was already disputed.", level="info", service_type=SERVICE_TYPE)
        return jsonify({"error": "Match already disputed."}), 403

    response = delete_match(None, pvp_match_uuid)

    if response[1] == 404:
        send_log(f"delete_match: No match found with uuid: {pvp_match_uuid} by user {session['username']}.", level="info", service_type=SERVICE_TYPE)
        return response
    elif response[1] == 200:
        send_log(f"reject_pv_prequest: User {session['username']} has successfully rejected match {pvp_match_uuid}.", level="general", service_type=SERVICE_TYPE)
        return jsonify({"message": "Match rejected successfully."}), 200
    else:
        send_log(f"delete_match: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
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
            params = {"uuid": user_uuid}
            url = "https://service_profile/profile/internal/exists"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config["requests_timeout"])
            response.raise_for_status()
            return response.json()

        exist_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        send_log(f"make_request_to_profile_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_profile_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_profile_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    if exist_data["exists"] == False:
        return jsonify({"error": "User not found."}), 404

    try:

        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"user_uuid": session["uuid"]}
            payload = {"team": team}
            url = "https://service_inventory/inventory/internal/check_owner_of_team"
            response = requests.post(
                url, params=params, json=payload, verify=False, timeout=current_app.config["requests_timeout"]
            )
            response.raise_for_status()

        make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            send_log(f"make_request_to_inventory_service: Some items not found in user {session['username']} inventory", level="info", service_type=SERVICE_TYPE)
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            send_log(f"make_request_to_inventory_service: HttpError {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except requests.RequestException as e:
        send_log(f"make_request_to_inventory_service: RequestException {e} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        send_log(f"make_request_to_inventory_service: Circuit breaker is open for uuid {session['username']}.", level="warning", service_type=SERVICE_TYPE)
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
        send_log(f"insert_match: HttpError {response} for uuid {session['username']}.", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    send_log(f"send_pvp_request: User {session['username']} has successfully sent a match request to user {user_uuid}.", level="general", service_type=SERVICE_TYPE)
    return jsonify({"message": "Match request sent successfully."}), 200
