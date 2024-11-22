import logging
import connexion
import uuid
import bcrypt
import json
import requests
import random
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests
from openapi_server.models.pv_p_request import PvPRequest
from openapi_server.models.team import Team
from openapi_server import util

from flask import current_app, jsonify, request, session
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])


def health_check():
    return jsonify({"message": "Service operational."}), 200


def accept_pvp_request(pvp_match_uuid): # TODO
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    user_uuid = session['uuid']

    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        cursor.execute(
            'SELECT BIN_TO_UUID(match_uuid), BIN_TO_UUID(player_1_uuid), BIN_TO_UUID(player_2_uuid), winner, timestamp, gachas_types_used FROM pvp_matches WHERE BIN_TO_UUID(match_uuid) = %s',
            (pvp_match_uuid,)
        )
        _, player1_uuid, player2_uuid, winner, _, teams = cursor.fetchone()  # teams initially contains team of player 1

        if player2_uuid != user_uuid:
            return jsonify({"error": "This request is not for you"}), 403

        if winner is not None:
            return jsonify({"error": "Match already ended"}), 403

        if connexion.request.is_json:
            body_request = connexion.request.get_json()
            team = body_request.get("gachas")

        if len(team) != 7:
            return jsonify({"error": "Exactly 7 gacha items required"}), 400

        # Construct query with placeholders for the 7 UUIDs
        placeholders = ', '.join(['%s'] * len(team))
        query = f'SELECT DISTINCT BIN_TO_UUID(owner_uuid) FROM inventories WHERE BIN_TO_UUID(item_uuid) IN ({placeholders})'
        
        # Execute query with the gacha UUIDs
        cursor.execute(query, tuple(team))
        owner_uuids = cursor.fetchall()
        
        # FIX: Correctly check that all items belong to the user
        owner_uuid = owner_uuids[0][0]
        
        if owner_uuid != user_uuid:
            return jsonify({"error": "Gacha items do not belong to you"}), 400

        # Deserialize `teams` if it was stored as a JSON string in the database
        if isinstance(teams, str):
            teams = json.loads(teams)

        # Extract `player1_team` and `player2_team`
        player1_team = teams if isinstance(teams, list) else teams.get("gachas", [])# Extract player 1's team
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
            
            # /db_manager/pvp/get_gacha_stat
            cursor.execute(
                f'SELECT gt.name, gt.{extracted_stat}, gt.stat_potential FROM inventories i JOIN gachas_types gt ON i.stand_uuid = gt.uuid WHERE i.item_uuid IN (UUID_TO_BIN(%s), UUID_TO_BIN(%s))',
                (player1_team[i], player2_team[i])
            )
            result = cursor.fetchall()
            #print (result)
            # Store data in variables for comparison
            player1_stand_name, player1_stand_stat, player1_stand_potential = result[0]
            player2_stand_name, player2_stand_stat, player2_stand_potential = result[1]

            log["pairings"].append({
                "pair": f"player1 {player1_stand_name} vs player2 {player2_stand_name}",
                "extracted_stat": extracted_stat,
                "player1": {
                    "stand_stat": player1_stand_stat
                },
                "player2": {
                    "stand_stat": player2_stand_stat
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
            winner = 0
            log["winner"] = player1_uuid + " by " + str(points) + " points "
        else:
            winner = 1
            log["winner"] = user_uuid + " by " + str(points * -1) + " points "

        log_json = json.dumps(log)

        # /db_manager/pvp/set_match_results
        cursor.execute(
            'UPDATE pvp_matches SET winner = %s, match_log = %s, timestamp = CURRENT_TIMESTAMP, gachas_types_used = %s WHERE match_uuid = UUID_TO_BIN(%s)',
            (winner, log_json, json.dumps(teams), pvp_match_uuid)  # FIX: Use json.dumps directly for teams
        )

        # Update pvp_score for the winner in the database
        if winner == 0:
            cursor.execute(
                'UPDATE profiles SET pvp_score = pvp_score + %s WHERE uuid = UUID_TO_BIN(%s)',
                (points, player1_uuid)
            )
        else:
            cursor.execute(
                'UPDATE profiles SET pvp_score = pvp_score + %s WHERE uuid = UUID_TO_BIN(%s)',
                (points, user_uuid)
            )

        connection.commit()

        return jsonify({"message": "Match accepted and performed successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()


def check_pending_pvp_requests(): # TODO done, but waiting for new mock data for test
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    payload = {
        "user_uuid": session["uuid"]
    } 

    # valid request from now on
    try:

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/pvp/check_pending_pvp_requests"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        requests_list = make_request_to_dbmanager()

        return requests_list, 200
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
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
            url = "http://db_manager:8080/db_manager/pvp/get_pvp_status"
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
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503


def reject_pv_prequest(pvp_match_uuid): # TODO done, but waiting for new mock data for test
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
            url = "http://db_manager:8080/db_manager/pvp/reject_pvp_request"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        make_request_to_dbmanager()

        return jsonify({"message": "Battle rejected successfully."}), 200
    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 404:
            return jsonify({"error": "Cannot reject this PvP request."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
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
            url = "http://db_manager:8080/db_manager/pvp/verify_gacha_item_ownership"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        player1_uuid = make_request_to_dbmanager()
        
        if player1_uuid != session['uuid']:
            return jsonify({"error": "Gacha items do not belong to you"}), 401

    except requests.HTTPError as e:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        if e.response.status_code == 401:
            return jsonify({"error": "Gacha items do not belong to you."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503

    
    try:
        match_uuid = uuid.uuid4()
        payload = {
            "pvp_match_uuid": match_uuid,
            "sender_id": session['uuid'],
            "receiver_id": user_uuid,
            "teams": {
                "team1": team,
                "team2": None
            },
            "winner": None,
            "match_log": None
        }

        @circuit_breaker
        def make_request_to_dbmanager():
            url = "http://db_manager:8080/db_manager/pvp/finalize_pvp_request_sending"
            response = requests.post(url, json=payload)
            response.raise_for_status()  # if response is obtained correctly
            return response.json()

        player1_uuid = make_request_to_dbmanager()
    except requests.HTTPError:  # if request is sent to dbmanager correctly and it answers an application error (to be managed here) [error expected by us]
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:  # if request is NOT sent to dbmanager correctly (is down) [error not expected]
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:  # if request already failed multiple times, the circuit breaker is open and this code gets executed
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503