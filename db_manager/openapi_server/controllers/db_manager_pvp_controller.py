import connexion
import logging
import json
import uuid
from datetime import date
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.ban_user_profile_request import BanUserProfileRequest
from openapi_server.models.get_gacha_stat200_response import GetGachaStat200Response
from openapi_server.models.get_gacha_stat_request import GetGachaStatRequest
from openapi_server.models.get_pvp_status_request import GetPvpStatusRequest
from openapi_server.models.match_requests_inner import MatchRequestsInner
from openapi_server.models.pv_p_request_full import PvPRequestFull
from openapi_server.models.reject_pvp_prequest_request import RejectPvpPrequestRequest
from openapi_server.models.set_match_results_request import SetMatchResultsRequest
from openapi_server.models.verify_gacha_item_ownership_request import VerifyGachaItemOwnershipRequest
from openapi_server import util

from flask import jsonify
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.db import get_db


circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def check_pending_pvp_requests(ban_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400

    # valid json request
    ban_user_profile_request = BanUserProfileRequest.from_dict(connexion.request.get_json())
    user_uuid = ban_user_profile_request.user_uuid

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            check_query = '''
            SELECT BIN_TO_UUID(match_uuid), BIN_TO_UUID(player_1_uuid), BIN_TO_UUID(player_2_uuid)
            FROM pvp_matches
            WHERE BIN_TO_UUID(player_2_uuid) = %s AND winner IS NULL;
            '''
            cursor.execute(check_query, (user_uuid,))
            connection.commit()
            return cursor.fetchall()
    
        # Fetch results from the database
        results = make_request_to_db()
        
        # Format the results
        formatted_results = [
            {
                "pvp_match_uuid": match_uuid,
                "from": player_1_uuid
            }
            for match_uuid, player_1_uuid, _ in results
        ]

        print(formatted_results)
        
        return formatted_results, 200

    except OperationalError: 
        logging.error("Query 1 [" + user_uuid + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query 1 ["+ user_uuid +"]: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query 1 ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query 1 ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query 1 ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def finalize_pvp_request_sending(pv_p_request_full=None):
    if not connexion.request.is_json:
        return "", 400

    # valid json request
    pv_p_request_full = PvPRequestFull.from_dict(connexion.request.get_json())
    match_uuid = pv_p_request_full.pvp_match_uuid
    player1_uuid = pv_p_request_full.sender_id
    user_uuid = pv_p_request_full.receiver_id
    teams = pv_p_request_full.teams

    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            check_query = '''
                SELECT COUNT(*) 
                FROM profiles 
                WHERE BIN_TO_UUID(uuid) = %s;
            '''
            cursor.execute(check_query, (user_uuid,))
            return cursor.fetchone()
        
        result = make_request_to_db()
        if result[0] != 1:
            return "", 404
        
    except OperationalError: 
        logging.error("Query 1 ["+ user_uuid + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query 1 ["+ user_uuid +"]: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query 1 ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query 1 ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query 1 ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            insert_query = '''
                INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, gachas_types_used)
                VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s, %s);
            '''
            cursor.execute(insert_query, (match_uuid, player1_uuid, user_uuid, None, None, jsonify(teams).get_data(as_text=True)))
            connection.commit()

        make_request_to_db()
        return "", 200

    except OperationalError: 
        logging.error("Query 2 ["+ user_uuid + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query 2 ["+ user_uuid +"]: Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query 2 ["+ user_uuid +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 500
    except InternalError:
        logging.error("Query 2 ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query 2 ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query 2 ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_gacha_stat(get_gacha_stat_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_gacha_stat_request = GetGachaStatRequest.from_dict(connexion.request.get_json())

    player1_item_uuid = get_gacha_stat_request.player1_stand
    player2_item_uuid = get_gacha_stat_request.player2_stand
    extracted_stat = get_gacha_stat_request.extracted_stat
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                f'SELECT gt.name, gt.{extracted_stat}, gt.stat_potential FROM inventories i JOIN gachas_types gt ON i.stand_uuid = gt.uuid WHERE i.item_uuid IN (UUID_TO_BIN(%s), UUID_TO_BIN(%s))',
                (player1_item_uuid, player2_item_uuid)
            )
            result = cursor.fetchall()
            if cursor.rowcount != 2:
                "", 404
            return result, 200
        
        gachas, code = make_request_to_db()

        if code != 200:
            return "", code

        response = {
            "player1_stat": gachas[0],
            "player2_stat": gachas[1]
        }
        
        return jsonify(response), 200

    except OperationalError: 
        logging.error("Query : Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query : Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query : Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query : Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query : Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_pvp_status(get_pvp_status_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    get_pvp_status_request = GetPvpStatusRequest.from_dict(connexion.request.get_json())
    pvp_match_uuid = get_pvp_status_request.pvp_match_uuid

    try:
        @circuit_breaker
        def make_request_to_db():
            player1_uuid = None
            player2_uuid = None
            winner = None
            match_log = None
            timestamp = None

            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT BIN_TO_UUID(player_1_uuid), BIN_TO_UUID(player_2_uuid), winner, match_log, timestamp FROM pvp_matches WHERE match_uuid = UUID_TO_BIN(%s)',
                (pvp_match_uuid,)
            )
            result = cursor.fetchone()
            if result:
                player1_uuid, player2_uuid, winner, match_log, timestamp = result
            
            return player1_uuid, player2_uuid, winner, match_log, timestamp


        player1_uuid, player2_uuid, winner, match_log, timestamp = make_request_to_db()
        
        if player1_uuid is None:
            return "", 404

        if winner is not None:
            if winner == 0:
                winner_uuid = player1_uuid
            else:
                winner_uuid = player2_uuid
            response = {
                "pvp_match_uuid": pvp_match_uuid,
                "sender_id": player1_uuid,
                "receiver_id": player2_uuid,
                "winner_id": winner_uuid,
                "match_log": json.loads(match_log),
                "match_timestamp": timestamp
            }
        else:
            response = {
                "pvp_match_uuid": pvp_match_uuid,
                "sender_id": player1_uuid,
                "receiver_id": player2_uuid,
                "winner_id": None,
                "match_log": None,
                "match_timestamp": timestamp
            }
        
        return response, 200

    except OperationalError: 
        logging.error("Query [" + pvp_match_uuid + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ pvp_match_uuid +"]: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query ["+ pvp_match_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ pvp_match_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ pvp_match_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def reject_pvp_prequest(reject_pvp_prequest_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    reject_pvp_prequest_request = RejectPvpPrequestRequest.from_dict(connexion.request.get_json())
    pvp_match_uuid = reject_pvp_prequest_request.pvp_match_uuid
    user_uuid = reject_pvp_prequest_request.user_uuid
    
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            delete_query = '''
                DELETE FROM pvp_matches 
                WHERE BIN_TO_UUID(match_uuid) = %s AND player_2_uuid = UUID_TO_BIN(%s) AND winner IS NULL;
            '''
            cursor.execute(delete_query, (pvp_match_uuid, user_uuid))
            connection.commit()
            return cursor.rowcount
        
        if make_request_to_db() == 0:
            return "", 404
    
        return "", 200

    except OperationalError: 
        logging.error("Query [" + pvp_match_uuid + ", " + user_uuid + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ pvp_match_uuid + ", " + user_uuid + "]: Programming error.")
        return "", 400
    except InternalError:
        logging.error("Query ["+ pvp_match_uuid + ", " + user_uuid + "]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ pvp_match_uuid + ", " + user_uuid + "]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ pvp_match_uuid + ", " + user_uuid + "]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def set_match_results(set_match_results_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    set_match_results_request = SetMatchResultsRequest.from_dict(connexion.request.get_json())

    pvp_match = set_match_results_request.match
    points = set_match_results_request.points

    winner = pvp_match["winner"]
    match_log = pvp_match["match_log"]
    teams = pvp_match["teams"]
    match_uuid = pvp_match["pvp_match_uuid"]
    player1_uuid = pvp_match["sender_id"]
    player2_uuid = pvp_match["receiver_id"]

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE pvp_matches SET winner = %s, match_log = %s, timestamp = CURRENT_TIMESTAMP, gachas_types_used = %s WHERE match_uuid = UUID_TO_BIN(%s)',
                (winner, match_log, teams, match_uuid)  # FIX: Use json.dumps directly for teams
            )

            # Update pvp_score for the winner in the database
            if winner:
                cursor.execute(
                    'UPDATE profiles SET pvp_score = pvp_score + %s WHERE uuid = UUID_TO_BIN(%s)',
                    (points, player1_uuid)
                )
            else:
                cursor.execute(
                    'UPDATE profiles SET pvp_score = pvp_score + %s WHERE uuid = UUID_TO_BIN(%s)',
                    (points, player2_uuid)
                )
            cursor.commit()
            return
        
        make_request_to_db()

        return "", 200
        
    except OperationalError: 
        logging.error("Query : Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query : Programming error.")
        return "", 400
    except InternalError:
        logging.error("Query : Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query : Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query : Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def verify_gacha_item_ownership(verify_gacha_item_ownership_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    verify_gacha_item_ownership_request = VerifyGachaItemOwnershipRequest.from_dict(connexion.request.get_json())
    team = verify_gacha_item_ownership_request.team
    team = tuple(team.strip('()').split(','))
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            placeholders = ', '.join(['%s'] * len(team))
            query = f'SELECT DISTINCT BIN_TO_UUID(owner_uuid) FROM inventories WHERE BIN_TO_UUID(item_uuid) IN ({placeholders})'
            # Execute query with the gacha UUIDs
            cursor.execute(query, team)
            result = cursor.fetchall()
            return result
        
        owner_uuid = make_request_to_db()

        if len(owner_uuid) != 1:
            return "", 401
        
        player1_uuid=owner_uuid[0][0]
        
        return player1_uuid, 200

    except OperationalError: 
        logging.error("Query [" + team + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ team + "]: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query ["+ team + "]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ team + "]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ team + "]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503