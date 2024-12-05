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

MOCK_PVPMATCHES = {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": {
        "pvp_match_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "sender_id": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "teams": {
            "team1": ["1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76"],
            "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"]
        },
        "winner": True,
        "match_log": {
            "rounds": [
                {
                    "extracted_stat": "power",
                    "player1": {
                        "stand_name": "Jotaro StarPlatinum",
                        "stand_stat": "A"
                    },
                    "player2": {
                        "stand_name": "DIO TheWorld",
                        "stand_stat": "A"
                    },
                    "round_winner": "Player1's Jotaro StarPlatinum"
                }
            ]
        },
        "match_timestamp": "2024-01-15T12:00:00Z"
    },
    "b2c3d4e5-f6a7-8901-bcde-f12345678901": {
        "pvp_match_uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "sender_id": "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "teams": {
            "team1": ["b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85"],
            "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"]
        },
        "winner": False,
        "match_log": {
            "rounds": [
                {
                    "extracted_stat": "potential",
                    "player1": {
                        "stand_name": "Giorno GoldExperience",
                        "stand_stat": "A"
                    },
                    "player2": {
                        "stand_name": "DIO TheWorld",
                        "stand_stat": "A"
                    },
                    "round_winner": "Player1's Giorno GoldExperience"
                }
            ]
        },
        "match_timestamp": "2024-01-16T15:30:00Z"
    },
    "d51729c7-7674-4e62-86b5-70b028d686d5": {
        "pvp_match_uuid": "d51729c7-7674-4e62-86b5-70b028d686d5",
        "sender_id": "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "receiver_id": "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "teams": {
            "team1": ["57b6c5d4-e3f2-1098-7654-fedcba987661","47b6c5d4-e3f2-1098-7654-fedcba987662", "37b6c5d4-e3f2-1098-7654-fedcba987663", "27b6c5d4-e3f2-1098-7654-fedcba987664","17b6c5d4-e3f2-1098-7654-fedcba987665","07b6c5d4-e3f2-1098-7654-fedcba987666","f6b6c5d4-e3f2-1098-7654-fedcba987667"],
            "team2": [""]
        },
        "winner": None,
        "match_log": {},
        "match_timestamp": "2024-01-15T12:00:00Z"
    }
}

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
            global MOCK_PVPMATCHES

            if uuid not in MOCK_PVPMATCHES:
                return 404  

            del MOCK_PVPMATCHES[uuid]

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
        return "", 503


def get_pending_list(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def pending_list():
            global MOCK_PVPMATCHES

            result = [
                (match_details["pvp_match_uuid"], match_details["sender_id"])
                for match_id, match_details in MOCK_PVPMATCHES.items()
                if match_details["receiver_id"] == uuid and match_details["winner"] == None
            ]
            return result

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
        return "", 503

def get_status(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def get_match():
            global MOCK_PVPMATCHES

            match_details = MOCK_PVPMATCHES.get(uuid)

            if not match_details:
                return None  # Equivalent to returning None when no match found in the original query

            # Create a tuple similar to the output from SQL query
            match_data = (
                match_details["pvp_match_uuid"],
                match_details["sender_id"],
                match_details["receiver_id"],
                match_details["winner"],
                str(match_details["match_log"]),
                match_details["match_timestamp"],
                match_details["teams"]
            )
            
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
            global MOCK_PVPMATCHES

            MOCK_PVPMATCHES[match_uuid] = {
                "pvp_match_uuid": match_uuid,
                "sender_id": player1_uuid,
                "receiver_id": player2_uuid,
                "teams": teams_json,
                "winner_id": winner,
                "match_log": match_log_json,
                "match_timestamp": timestamp
            }

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
        return "", 503


def remove_by_user_uuid(session=None, uuid=None):
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def remove_match():
            global MOCK_PVPMATCHES

            matches_to_delete = [
                match_id for match_id, match_details in MOCK_PVPMATCHES.items()
                if match_details["sender_id"] == uuid or match_details["receiver_id"] == uuid
            ]            

            for match_id in matches_to_delete:
                del MOCK_PVPMATCHES[match_id]

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
            global MOCK_PVPMATCHES

            if match_uuid in MOCK_PVPMATCHES:
                MOCK_PVPMATCHES[match_uuid]["winner_id"] = winner

                MOCK_PVPMATCHES[match_uuid]["match_log"] = match_log_json

                MOCK_PVPMATCHES[match_uuid]["teams"] = teams_json

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
        return "", 503
