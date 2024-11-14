import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server.models.team import Team  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def accept_pvp_request(pvp_match_uuid, team, session=None):  # noqa: E501
    """Accept a pending PvP request.

    Allows a player to accept a PvP battle with another user. # noqa: E501

    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str
    :param team: Specify the team to battle the player with.
    :type team: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        team = Team.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def check_pending_pvp_requests(session=None):  # noqa: E501
    """Returns a list of pending PvP requests.

    If the current user has one or more pending requests, a list will be returned. The current user&#39;s UUID is obtained via session cookie. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[PendingPvPRequests, Tuple[PendingPvPRequests, int], Tuple[PendingPvPRequests, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pvp_status(pvp_match_uuid):  # noqa: E501
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    try:

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        
        cursor.execute(
            'SELECT match_uuid, BIN_TO_UUID(player_1_uuid), BIN_TO_UUID(player_2_uuid), winner, match_log, timestamp, gachas_types_used FROM pvp_matches WHERE match_uuid = UUID_TO_BIN(%s)',
            (pvp_match_uuid,)
        )
        _ , player1_uuid, player2_uuid, winner, match_log, timestamp, gacha_used = cursor.fetchone()
        
        if winner is not None:
            if winner == 0:
                winner_uuid = player1_uuid
            else:
                winner_uuid = player2_uuid
        
        response = {
            "player1": player1_uuid,
            "player2": player2_uuid,
            "winner": winner_uuid,
            "match log": match_log,
            "request_timestamp": timestamp,
            "gacha_used": gacha_used,
        }
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error":str(e)}), 500

    finally:
        cursor.close()
        connection.close()


def reject_pv_prequest(pvp_match_uuid, session=None):  # noqa: E501
    """Rejects a pending PvP request.

    Allows a player to reject a PvP battle with another user. # noqa: E501

    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def send_pvp_request(user_uuid, team):  # noqa: E501
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    print("ok")
    # Extract gacha UUIDs from the team parameter
    gacha_uuids = []
    for gacha in team['gachas']:
        _, uuid = gacha.popitem()  # _ is the key, uuid is the value
        gacha_uuids.append(uuid)

    print(gacha_uuids)

    if len(gacha_uuids) != 7:
        return jsonify({"error": "Exactly 7 gacha items required"}), 400

    try:

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # Construct query with placeholders for the 7 UUIDs
        placeholders = ', '.join(['%s'] * len(gacha_uuids))
        query = f'SELECT DISTINCT owner_uuid FROM inventories WHERE item_id IN ({placeholders})'
        
        # Execute query with the gacha UUIDs
        cursor.execute(query, tuple(gacha_uuids))
        owner_uuids = cursor.fetchall()

        if len(owner_uuids) != 1:
            return jsonify({"error": "Gacha items do not belong to you"}), 400
        
        player1_uuid=owner_uuids[0]
        #CHECK IF IT'S USER_UUID

        check_query = '''
            SELECT COUNT(*) 
            FROM profiles 
            WHERE uuid = %s;
        '''
        cursor.execute(check_query, (user_uuid,))
        result = cursor.fetchone()

        if result[0] != 1:
            return jsonify({"error": "Player 2 not found in profiles"}), 404

        # Step 2: Insert the new match into the pvp_matches table
        insert_query = '''
            INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, gachas_types_used)
            VALUES (%s, %s, %s, %s, %s, %s);
        '''
        cursor.execute(insert_query, (uuid.uuid4(), player1_uuid, user_uuid, None, None, team))

        return jsonify({"message":"Match request sent successfully."}), 200

    except Exception as e:
        return jsonify({"error":str(e)}), 500

    finally:
        cursor.close()
        connection.close()
