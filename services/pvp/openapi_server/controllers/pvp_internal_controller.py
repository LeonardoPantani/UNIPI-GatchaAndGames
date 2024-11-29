import connexion
import json
from typing import Dict
from typing import Tuple
from typing import Union

from pybreaker import CircuitBreaker, CircuitBreakerError
from flask import jsonify, session
import requests
import logging
from datetime import datetime

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server import util

from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from openapi_server.helpers.db import get_db

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5)


def delete_match(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def remove_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT *
                FROM pvp_matches
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query,(uuid,))
            if not cursor.fetchone():
                return 404

            query = """
                DELETE 
                FROM pvp_matches
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,))

            connection.commit()
            cursor.close()

            return 200

        status_code = remove_match()

        if status_code == 404:
            return jsonify({"error":"Match not found."}), 404 

        return jsonify({"message":"Match deleted."}), 200

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



def get_pending_list(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def pending_list():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(match_uuid), BIN_TO_UUID(player_1_uuid)
                FROM pvp_matches
                WHERE player_2_uuid = UUID_TO_BIN(%s)
                AND winner IS NULL
            """

            cursor.execute(query,(uuid,))
            match_data = cursor.fetchall()

            cursor.close()

            return match_data
        
        match_list = pending_list()

        response = []
        for match in match_list:
            payload = {
                "pvp_match_id": match[0],
                "from": match[1]
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


def get_status(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def get_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(match_uuid), BIN_TO_UUID(player_1_uuid), BIN_TO_UUID(player_2_uuid), winner, match_log, timestamp, gachas_types_used
                FROM pvp_matches
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query,(uuid,))
            match_data = cursor.fetchone()

            cursor.close()

            return match_data
        
        match = get_match()

        response = {
            "pvp_match_uuid": match[0],
            "sender_id": match[1],
            "receiver_id": match[2],
            "teams": match[6],
            "winner_id": match[1] if match[3] else match[2],
            "match_log": match[4],
            "match_timestamp": match[5]
        }

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


def insert_match(pv_p_request=None, session=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
        
    pv_p_request = PvPRequest.from_dict(connexion.request.get_json())  # noqa: E501
    
    match_uuid = pv_p_request.pvp_match_uuid
    player1_uuid = pv_p_request.sender_id
    player2_uuid = pv_p_request.receiver_id
    teams = pv_p_request.teams
    winner = True if pv_p_request.winner_id == player1_uuid else False
    match_log = pv_p_request.match_log
    timestamp = pv_p_request.match_timestamp

    if not match_uuid or not player1_uuid or not player2_uuid or not teams or not timestamp:
        return "", 400
    
    match_log_json = json.dumps(match_log.to_dict())
    teams_json = json.dumps(teams.to_dict())

    try:
        @circuit_breaker
        def insert_pvp_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                INSERT INTO pvp_matches 
                (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, timestamp, gachas_types_used)
                VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s, %s, %s)
            """

            cursor.execute(query,(match_uuid, player1_uuid, player2_uuid, winner, match_log_json, timestamp, teams_json))

            connection.commit()
            cursor.close()

        insert_pvp_match()

        return jsonify({"message":"Match inserted"}), 201

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
    except DatabaseError:
        logging.error(f"Query: Generic database error.")
        return "", 503
    except CircuitBreakerError:
        return "", 503


def remove_by_user_uuid(session=None, uuid=None):  # noqa: E501
    if not uuid:
        return "", 400
    
    try:
        @circuit_breaker
        def remove_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                DELETE 
                FROM pvp_matches
                WHERE player_1_uuid = UUID_TO_BIN(%s)
                OR player_2_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (uuid,uuid))

            connection.commit()
            cursor.close()

        remove_match()

        return jsonify({"message":"Match deleted."}), 200

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


def set_results(pv_p_request=None, session=None):  # noqa: E501
    if not connexion.request.is_json:
        return "", 400
    
    pv_p_request = PvPRequest.from_dict(connexion.request.get_json())  # noqa: E501

    match_uuid = pv_p_request.pvp_match_uuid
    player1_uuid = pv_p_request.sender_id
    player2_uuid = pv_p_request.receiver_id
    teams = pv_p_request.teams
    winner = True if pv_p_request.winner_id == player1_uuid else False
    match_log = pv_p_request.match_log
    timestamp = pv_p_request.match_timestamp

    if not match_uuid or not player1_uuid or not player2_uuid or not teams or not timestamp:
        return "", 400
    
    match_log_json = json.dumps(match_log.to_dict())
    teams_json = json.dumps(teams.to_dict())

    try:
        @circuit_breaker
        def update_match():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                UPDATE pvp_matches
                SET winner = %s, match_log = %s, gachas_types_used = %s
                WHERE match_uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(query, (winner, match_log_json, teams_json, match_uuid))

            connection.commit()
            cursor.close()

        update_match()

        return jsonify({"message":"Match updated."}), 200

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