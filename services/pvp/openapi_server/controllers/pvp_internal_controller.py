import json

import connexion
from flask import jsonify
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

from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.models.pending_pv_p_requests import PendingPvPRequests
from openapi_server.models.pv_p_request import PvPRequest

SERVICE_TYPE = "pvp"
circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=5,
    exclude=[
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ],
)


def delete_match(session=None, uuid=None):
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

            cursor.execute(query, (uuid,))
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
            return jsonify({"error": "Match not found."}), 404

        return jsonify({"message": "Match deleted."}), 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_pending_list(session=None, uuid=None):
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

            cursor.execute(query, (uuid,))
            match_data = cursor.fetchall()

            cursor.close()

            return match_data

        match_list = pending_list()

        response = []
        for match in match_list:
            payload = {"pvp_match_id": match[0], "from": match[1]}
            response.append(payload)

        return jsonify(response), 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_status(session=None, uuid=None):
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

            cursor.execute(query, (uuid,))
            match_data = cursor.fetchone()

            cursor.close()

            return match_data

        match = get_match()

        if not match:
            return jsonify({"error": "Match not found"}), 404

        if match[3] is None:
            winner_id = ""
        elif match[3]:
            winner_id = match[1]
        else:
            winner_id = match[2]

        response = {
            "pvp_match_uuid": match[0],
            "sender_id": match[1],
            "receiver_id": match[2],
            "teams": match[6],
            "winner_id": winner_id,
            "match_log": match[4],
            "match_timestamp": match[5],
        }

        return jsonify(response), 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def insert_match(pv_p_request=None, session=None):
    if pv_p_request is None:
        if not connexion.request.is_json:
            return "", 400
        pv_p_request = PvPRequest.from_dict(connexion.request.get_json()).to_dict()

    match_uuid = pv_p_request["pvp_match_uuid"]
    player1_uuid = pv_p_request["sender_id"]
    player2_uuid = pv_p_request["receiver_id"]
    teams = pv_p_request["teams"]
    match_log = pv_p_request["match_log"]
    timestamp = pv_p_request["match_timestamp"]

    if pv_p_request["winner_id"] == player1_uuid:
        winner = True
    elif pv_p_request["winner_id"] == player2_uuid:
        winner = False
    else:
        winner = None
    
    if not match_uuid or not player1_uuid or not player2_uuid or not teams or not timestamp:
        return "", 400

    match_log_json = json.dumps(match_log)
    teams_json = json.dumps(teams)

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

            cursor.execute(
                query, (match_uuid, player1_uuid, player2_uuid, winner, match_log_json, timestamp, teams_json)
            )

            connection.commit()
            cursor.close()

        insert_pvp_match()

        return jsonify({"message": "Match inserted"}), 201

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def remove_by_user_uuid(session=None, uuid=None):
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

            cursor.execute(query, (uuid, uuid))

            connection.commit()
            cursor.close()

        remove_match()

        return jsonify({"message": "Match deleted."}), 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def set_results(pv_p_request=None, session=None):    
    if pv_p_request is None:
        if not connexion.request.is_json:
            return "", 400
        pv_p_request = PvPRequest.from_dict(connexion.request.get_json()).to_dict()

    match_uuid = pv_p_request["pvp_match_uuid"]
    player1_uuid = pv_p_request["sender_id"]
    player2_uuid = pv_p_request["receiver_id"]
    teams = pv_p_request["teams"]
    winner = True if pv_p_request["winner_id"] == player1_uuid else False
    match_log = pv_p_request["match_log"]
    timestamp = pv_p_request["match_timestamp"]

    if not match_uuid or not player1_uuid or not player2_uuid or not teams or not timestamp:
        return "", 400

    match_log_json = json.dumps(match_log)
    teams_json = json.dumps(teams)

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

        return jsonify({"message": "Match updated."}), 200

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"PvP_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503
