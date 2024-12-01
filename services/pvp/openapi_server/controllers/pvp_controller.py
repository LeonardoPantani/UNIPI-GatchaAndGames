import logging
import connexion
import uuid
import json
import requests
import random
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests_inner import PendingPvPRequestsInner
from openapi_server.models.pending_pv_p_requests import PendingPvPRequests
from openapi_server.models.pv_p_request import PvPRequest
from openapi_server.models.team import Team
from openapi_server import util
from openapi_server.helpers.logging import send_log

from flask import jsonify, request, session
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])


def pvp_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def accept_pvp_request(pvp_match_uuid): 
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    user_uuid = session['uuid']

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "pvp_match_uuid": pvp_match_uuid
            }
            url = "https://db_manager/db_manager/pvp/get_pvp_status"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        match_request = make_request_to_dbmanager()

    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    player1_uuid = match_request["sender_id"]
    receiver_uuid = match_request["receiver_id"]

    if receiver_uuid != user_uuid:
        return jsonify({"error": "This request is not for you"}), 401
    
    winner = match_request["winner"]

    if winner is not None:
        return jsonify({"error": "Match already ended"}), 406

    if connexion.request.is_json:
        body_request = connexion.request.get_json()
        team = body_request.get("gachas")

    if len(team) != 7:
        return jsonify({"error": "Exactly 7 gacha items required"}), 400

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                    "pvp_match_uuid": pvp_match_uuid
            }
            url = "https://db_manager/db_manager/pvp/verify_gacha_item_ownership"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()
        
        player2_uuid = make_request_to_dbmanager()

    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
        
    if player2_uuid != user_uuid:
        return jsonify({"error": "Gacha items do not belong to you"}), 400

    # TODO riparare
    # Deserialize `teams` if it was stored as a JSON string in the database
    if isinstance(teams, str):
        teams = json.loads(teams)

    # Extract `player1_team` and `player2_team`
    player1_team = teams["teams"]["team1"] # Extract player 1's team
    player2_team = team  # `team` is already a list

    # Shuffle player 2's team
    random.shuffle(player2_team)

    stats = ["stat_power", "stat_speed", "stat_durability", "stat_precision", "stat_range"]
    points = 0
    log = {
        "pairings": []
    }

    for i in range(7):
        extracted_stat = random.choice(stats)  # FIX: Use random.choice instead of random.randint to get a random stat
        
        try:
            @circuit_breaker
            def make_request_to_dbmanager():
                payload = {
                    "player1_stand": player1_team[i],
                    "player2_stand": player2_team[i],
                    "extracted_stat": extracted_stat
                }
                url = "https://db_manager/db_manager/pvp/get_gacha_stat"
                response = requests.post(url, json=payload)
                response.raise_for_status()  # if response is obtained correctly
                return response.json()

            result = make_request_to_dbmanager()

        except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
            return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError: 
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

        # Store data in variables for comparison
        def number_to_stat(number):
            return chr(ord('A') + (5 - number))

        player1_stand_name, player1_stand_stat, player1_stand_potential = result["player1_stat"]
        player2_stand_name, player2_stand_stat, player2_stand_potential = result["player2_stat"]

        log["pairings"].append({
            str("Turn "+i): f"player1 {player1_stand_name} vs player2 {player2_stand_name}",
            "extracted_stat": extracted_stat,
            "player1": {
                "stand_stat": number_to_stat(player1_stand_stat)
            },
            "player2": {
                "stand_stat": number_to_stat(player2_stand_stat)
            }
        })

        if player1_stand_stat > player2_stand_stat:
            points += 1
        elif player1_stand_stat < player2_stand_stat:
            points -= 1
        else:
            if player1_stand_potential > player2_stand_potential:
                points += 1
            elif player1_stand_potential < player2_stand_potential:
                points -= 1
            else:
                points += random.choice([1, -1])

    if points > 0:
        winner = True
        log["winner"] = player1_uuid + " by " + str(points) + " points "
    else:
        winner = False
        log["winner"] = user_uuid + " by " + str(points * -1) + " points "

    log_json = json.dumps(log)

    try:
        @circuit_breaker
        def make_request_to_dbmanager():
            payload = {
                "match":{
                    "winner": winner,
                    "teams": {
                        "team1": player1_team,
                        "team2": player2_team
                    },
                    "match_log": log_json,
                    "receiver_id": player2_uuid,
                    "pvp_match_uuid": pvp_match_uuid,
                    "sender_id": player1_uuid
                },
                "points": points
            }
            url = "https://db_manager/db_manager/pvp/set_match_results"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return 
        
        make_request_to_dbmanager()
    
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Not found"}), 404
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


    return jsonify({"message": "Match accepted and performed successfully."}), 200



def check_pending_pvp_requests(): 
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    payload = {
        "user_uuid": session["uuid"]
    } 

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "https://db_manager/db_manager/pvp/check_pending_pvp_requests"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        requests_list = make_request_to_dbmanager()

        return requests_list, 200
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_pvp_status(pvp_match_uuid):
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    payload = {
        "pvp_match_uuid": pvp_match_uuid
    }

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "https://db_manager/db_manager/pvp/get_pvp_status"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        requests_list = make_request_to_dbmanager()

        return requests_list, 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Match not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def reject_pv_prequest(pvp_match_uuid): 
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    payload = {
        "pvp_match_uuid": pvp_match_uuid,
        "user_uuid": session["uuid"]
    }

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "https://db_manager/db_manager/pvp/reject_pvp_request"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Battle rejected successfully."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Cannot reject this PvP request."}), 401
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def send_pvp_request(user_uuid):
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    if session['uuid'] == user_uuid:
        return jsonify({"error": "You cannot start a match with yourself."}), 406

    team = connexion.request.get_json().get("gachas")

    # valid request from now on
    payload = {
        "team": "(" + ",".join(team) + ")"
    }

    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "https://db_manager/db_manager/pvp/verify_gacha_item_ownership"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        player1_uuid = make_request_to_dbmanager()
        
        if player1_uuid != session['uuid']:
            return jsonify({"error": "Gacha items do not belong to you"}), 401

    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 401:
            return jsonify({"error": "Gacha items do not belong to you."}), 401
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    try:
        match_uuid = str(uuid.uuid4())
        payload = {
            "pvp_match_uuid": match_uuid,
            "sender_id": session['uuid'],
            "receiver_id": user_uuid,
            "teams": {
                "team1": team,
                "team2": ["", "", "", "", "", "", ""]
            },
            "winner": True,
            "match_log": {}
        }
        
        @circuit_breaker
        def make_request_to_dbmanager():
            url = "https://db_manager/db_manager/pvp/finalize_pvp_request_sending"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message":"Match request sent successfully. UUID: "+ match_uuid}), 200
    
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError: 
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503