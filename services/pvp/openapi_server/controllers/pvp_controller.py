import logging
import connexion
import uuid
import json
import requests
import random
from typing import Dict
from typing import Tuple
from typing import Union
from datetime import datetime


from openapi_server.models.pending_pv_p_requests_inner import PendingPvPRequestsInner
from openapi_server.models.pending_pv_p_requests import PendingPvPRequests
from openapi_server.models.pv_p_request import PvPRequest
from openapi_server.models.team import Team
from openapi_server import util
from openapi_server.helpers.logging import send_log

from openapi_server.helpers.authorization import verify_login

from openapi_server.helpers.input_checks import sanitize_team_input, sanitize_uuid_input
from openapi_server.helpers.stats import map_number_to_grade

from openapi_server.controllers.pvp_internal_controller import set_results, get_pending_list, insert_match, delete_match, get_status

from flask import jsonify, request, session, current_app
from pybreaker import CircuitBreaker, CircuitBreakerError


circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError])

SERVICE_TYPE = "pvp"

def pvp_health_check_get():
    return jsonify({"message": "Service operational."}), 200

def accept_pvp_request(pvp_match_uuid): 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error":"Invalid input"}), 400
    
    response = get_status(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] != 200:
        return  jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    match_data = response

    sender_uuid = match_data["sender_id"]
    receiver_uuid = match_data["receiver_id"]

    if receiver_uuid != session['uuid']:
        return jsonify({"error": "This request is not for you"}), 401
    
    winner = match_data["winner"]

    if winner is not None:
        return jsonify({"error": "Match already ended"}), 406
    
    if not connexion.request.is_json:
        return jsonify({"error":"Invalid request."}), 400 

    player2_team = connexion.request.get_json()

    player2_team = sanitize_team_input(player2_team)
    if not player2_team:
        return jsonify({"error":"Invalid input"}), 400
    
    try:
        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"user_uuid": session['uuid']}
            payload = {"team": player2_team}
            url = "https://service_inventory/inventory/internal/check_owner_of_team"
            response = requests.post(url, params=params, json=payload, verify=False, timeout=current_app.config['requests_timeout'])
            response.raise_for_status()
        
        make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  
    
    player1_team = match_data['teams']['team1']

    random.shuffle(player2_team)

    stats = ["stat_power", "stat_speed", "stat_durability", "stat_precision", "stat_range"]
    points = 0
    log = {
        "rounds": []
    }

    for i in range(7):
        extracted_stat = random.choice(stats)

        try:
            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": player1_team[i]}
                url = "https://service_inventory/inventory/internal/get_stand_uuid_by_item_uuid"
                response = requests.get(url, params=params, verify=False, timeout=current_app.config['requests_timeout'])
                response.raise_for_status()
                return response.json()
            
            response_data = make_request_to_inventory_service()

            player1_stand = response_data['stand_uuid']

            @circuit_breaker
            def make_request_to_inventory_service():
                params = {"uuid": player2_team[i]}
                url = "https://service_inventory/inventory/internal/get_stand_uuid_by_item_uuid"
                response = requests.get(url, params=params, verify=False, timeout=current_app.config['requests_timeout'])
                response.raise_for_status()
                return response.json()
            
            response_data = make_request_to_inventory_service()

            player2_stand = response_data['stand_uuid']

        except requests.HTTPError as e:
            if e.response.status_code == 404: 
                return jsonify({"error": "Items not found in user inventory."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  
        
        try:
            @circuit_breaker
            def make_request_to_gacha_service():
                params = {"uuid": player1_stand}
                url = "https://service_inventory/gacha/internal/gacha/get"
                response = requests.get(url, params=params, verify=False, timeout=current_app.config['requests_timeout'])
                response.raise_for_status()
                return response.json()
            
            player1_stand_data = make_request_to_gacha_service()

            @circuit_breaker
            def make_request_to_gacha_service():
                params = {"uuid": player2_stand}
                url = "https://service_inventory/gacha/internal/gacha/get"
                response = requests.get(url, params=params, verify=False, timeout=current_app.config['requests_timeout'])
                response.raise_for_status()
                return response.json()
            
            player2_stand_data = make_request_to_gacha_service()

        except requests.HTTPError as e:
            if e.response.status_code == 404: 
                return jsonify({"error": "Gacha not found."}), 404
            else:
                return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
        except requests.RequestException:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
        except CircuitBreakerError:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503 

        player1_stand_name = player1_stand_data['name']
        player2_stand_name = player2_stand_data['name']
        player1_stand_potential = player1_stand_data['attributes']['potential']
        player2_stand_potential = player2_stand_data['attributes']['potential']
        player1_stand_stat = player1_stand_data['attributes'][extracted_stat.replace("stat_","")]
        player2_stand_stat = player2_stand_data['attributes'][extracted_stat.replace("stat_","")]

        if player1_stand_stat > player2_stand_stat:
            points += 1
            round_winner = "Player 1"
        elif player1_stand_stat < player2_stand_stat:
            points -= 1
            round_winner = "Player 2"
        else:
            if player1_stand_potential > player2_stand_potential:
                points += 1
                round_winner = "Player 1"
            elif player1_stand_potential < player2_stand_potential:
                points -= 1
                round_winner = "Player 2"
            else:
                random_choice = random.choice([1, -1])
                points += random_choice
                if random_choice > 0:
                    round_winner = "Player 1"
                else:
                    round_winner = "Player 2"

        log["rounds"].append(
            {
                "extracted_stat": extracted_stat.replace("stat_", ""),
                "player1": {
                    "stand_name": player1_stand_name,
                    "stand_stat": map_number_to_grade(player1_stand_stat)
                },
                "player2": {
                    "stand_name": player2_stand_name,
                    "stand_stat": map_number_to_grade(player2_stand_stat)
                },
                "round_winner": round_winner
            }
        )

    if points > 0:
        winner = True
        winner_id = sender_uuid
    else:
        winner = False
        winner_id = receiver_uuid

    log_json = json.dumps(log)

    payload = {
    "pvp_match_uuid": pvp_match_uuid,
    "sender_id": sender_uuid,
    "receiver_id": receiver_uuid,
    "teams": {
        "team1": player1_team,
        "team2": player2_team
    },
    "winner_id": winner_id,
    "match_log": {log_json},
    "match_timestamp": datetime.now()
    }

    response = set_results(payload, None)

    if response[1] == 200:
        return  response
    else:
        return  jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def check_pending_pvp_requests(): 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione

    response = get_pending_list(None, session['uuid'])

    if response[1] == 200:
        return  response
    else:
        return  jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

def get_pvp_status(pvp_match_uuid):
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione    

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error":"Invalid input"}), 400
    
    response = get_status(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] == 200:
        return  response
    else:
        return  jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

def reject_pv_prequest(pvp_match_uuid): 
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione    

    valid, pvp_match_uuid = sanitize_uuid_input(pvp_match_uuid)
    if not valid:
        return jsonify({"error":"Invalid input"}), 400

    response = delete_match(None, pvp_match_uuid)

    if response[1] == 404:
        return response
    elif response[1] == 200:
        return  jsonify({"message": "Match rejected successfully."}), 200
    else:
        return  jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def send_pvp_request(user_uuid):
    session = verify_login(connexion.request.headers.get('Authorization'), service_type=SERVICE_TYPE)
    if session[1] != 200: # se dà errore, il risultato della verify_login è: (messaggio, codice_errore)
        return session
    else: # altrimenti, va preso il primo valore (0) per i dati di sessione già pronti
        session = session[0]
    # fine controllo autenticazione    

    valid, user_uuid = sanitize_uuid_input(user_uuid)
    if not valid:
        return jsonify({"error":"Invalid input"}), 400

    if session['uuid'] == user_uuid:
        return jsonify({"error": "You cannot start a match with yourself."}), 406
    
    if not connexion.request.is_json:
        return jsonify({"error":"Invalid request."}), 400 

    team = connexion.request.get_json()

    team = sanitize_team_input(team)
    if not team:
        return jsonify({"error":"Invalid input"}), 400

    try:
        @circuit_breaker
        def make_request_to_profile_service():
            params = {"uuid": user_uuid}
            url = "https://service_profile/profile/internal/exists"
            response = requests.get(url, params=params, verify=False, timeout=current_app.config['requests_timeout'])
            response.raise_for_status()
            return response.json()
        
        exist_data = make_request_to_profile_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "User not found."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503
    
    if exist_data['exists'] == False:
        return jsonify({"error": "User not found."}), 404

    try:
        @circuit_breaker
        def make_request_to_inventory_service():
            params = {"user_uuid": session['uuid']}
            payload = {"team": team}
            url = "https://service_inventory/inventory/internal/check_owner_of_team"
            response = requests.post(url, params=params, json=payload, verify=False, timeout=current_app.config['requests_timeout'])
            response.raise_for_status()
        
        make_request_to_inventory_service()

    except requests.HTTPError as e:
        if e.response.status_code == 404: 
            return jsonify({"error": "Items not found in user inventory."}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service temporarily unavailable. Please try again later. [CircuitBreaker]"}), 503  

    match_uuid = str(uuid.uuid4())
    payload = {
        "pvp_match_uuid": match_uuid,
        "sender_id": session['uuid'],
        "receiver_id": user_uuid,
        "teams": {
            "team1": team,
            "team2": ["", "", "", "", "", "", ""]
        },
        "winner_id": "",
        "match_log": {},
        "match_timestamp": datetime.now()
    }

    response = insert_match(payload, None)
    
    if response[1] != 201:
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    
    return jsonify({"message": "Match request sent successfully."}), 200