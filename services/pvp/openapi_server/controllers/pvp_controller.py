import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.pending_pv_p_requests import PendingPvPRequests  # noqa: E501
from openapi_server.models.pv_p_request import PvPRequest  # noqa: E501
from openapi_server.models.team import Team  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
import uuid
import random

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def accept_pvp_request(pvp_match_uuid):  # noqa: E501
    
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
        _ , player1_uuid, player2_uuid, winner, _, teams = cursor.fetchone() #teams initially contains team of player 1

        if player2_uuid != user_uuid:
            return jsonify({"error": "This request is not for you"}), 403
        
        if winner != None:
            return jsonify({"error": "Match already ended"}), 403
        
        if connexion.request.is_json:
            body_request = connexion.request.get_json()
            team = body_request.get("gachas")

        if len(team) != 7:
            return jsonify({"error": "Exactly 7 gacha items required"}), 400
        
        # Construct query with placeholders for the 7 UUIDs
        placeholders = ', '.join(['%s'] * len(team))
        query = f'SELECT BIN_TO_UUID(owner_uuid) FROM inventories WHERE BIN_TO_UUID(item_uuid) IN ({placeholders})'
        
        # Execute query with the gacha UUIDs
        cursor.execute(query, tuple(team))
        owner_uuids = cursor.fetchall()[0]
        
        if len(owner_uuids) != 1:
            return jsonify({"error": "Gacha items do not belong to you"}), 400
        
        player1_team = teams.get("gachas",[])
        player2_team = team.get("gachas",[])

        teams['team1'] = teams.pop('gachas')
        teams['team2'] = team

        random.shuffle(player2_team)

        stats = ["stat_power", "stat_speed", "stat_durability", "stat_precision", "stat_range"]
        points = 0
        log = {
            "pairings": []
        }

        for i in range(7):
            extracted_stat = stats[random.randint(0,4)]

            cursor.execute(
                'SELECT gt.name, gt.%s, gt.stat_potential FROM inventories i JOIN gachas_types gt ON i.stand_uuid = gt.uuid WHERE i.item_uuid IN (UUID_TO_BIN(%s), UUID_TO_BIN(%s))',
                (extracted_stat, player1_team[i], player2_team[i])
            )
            result = cursor.fetchall()
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
                points+=1
            elif player1_stand_stat < player2_stand_stat:
                points-=1
            else:
                if player1_stand_potential > player2_stand_potential:
                    points+=1
                elif player1_stand_potential < player2_stand_potential:
                    points-=1
                else:
                    points+=random.choice([1, -1])

        if points > 0:
            winner = 0
            log["winner"] = player1_uuid
        else:
            winner = 1
            log["winner"] = user_uuid

        log_json = jsonify(log)
        print(log_json.get_data(as_text=True))

        cursor.execute(
            'UPDATE pvp_matches SET winner = %s, match_log = %s, timestamp = CURRENT_TIMESTAMP, gachas_types_used = %s WHERE match_uuid = UUID_TO_BIN(%s)',
            (winner, log_json, jsonify(teams), pvp_match_uuid)
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

        return jsonify({"message":"Match accepted and performed successfully."}), 200

    except Exception as e:
        return jsonify({"error":str(e)}), 500

    finally:
        cursor.close()
        connection.close()


def check_pending_pvp_requests(session):  # noqa: E501
    """Returns a list of pending PvP requests.

    If the current user has one or more pending requests, a list will be returned. The current user&#39;s UUID is obtained via session cookie. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[PendingPvPRequests, Tuple[PendingPvPRequests, int], Tuple[PendingPvPRequests, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_pvp_status(session, pvp_match_uuid):  # noqa: E501
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



def reject_pv_prequest(session, pvp_match_uuid):  # noqa: E501
    """Rejects a pending PvP request.

    Allows a player to reject a PvP battle with another user. # noqa: E501

    :param session: 
    :type session: str
    :param pvp_match_uuid: The pending pvp request&#39;s match id.
    :type pvp_match_uuid: str
    :type pvp_match_uuid: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def send_pvp_request(user_uuid):  # noqa: E501
    
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    # Extract gacha UUIDs from the team parameter
    if connexion.request.is_json:
        body_request = connexion.request.get_json()
        team = body_request.get("gachas")

    if len(team) != 7:
        return jsonify({"error": "Exactly 7 gacha items required"}), 400

    try:

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # Construct query with placeholders for the 7 UUIDs
        placeholders = ', '.join(['%s'] * len(team))
        query = f'SELECT BIN_TO_UUID(owner_uuid) FROM inventories WHERE BIN_TO_UUID(item_uuid) IN ({placeholders})'
        
        # Execute query with the gacha UUIDs
        cursor.execute(query, tuple(team))
        owner_uuids = cursor.fetchall()[0]
        print(owner_uuids)
        if len(owner_uuids) != 1:
            return jsonify({"error": "Gacha items do not belong to you"}), 400
        
        player1_uuid=owner_uuids[0]
        print(session['uuid'])
        if player1_uuid != session['uuid']:
            return jsonify({"error": "Gacha items do not belong to you"}), 400

        check_query = '''
            SELECT COUNT(*) 
            FROM profiles 
            WHERE BIN_TO_UUID(uuid) = %s;
        '''
        cursor.execute(check_query, (user_uuid,))
        result = cursor.fetchone()

        if result[0] != 1:
            return jsonify({"error": "Player 2 not found in profiles"}), 404

        # Step 2: Insert the new match into the pvp_matches table
        insert_query = '''
            INSERT INTO pvp_matches (match_uuid, player_1_uuid, player_2_uuid, winner, match_log, gachas_types_used)
            VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s, %s);
        '''
        cursor.execute(insert_query, (uuid.uuid4(), player1_uuid, user_uuid, None, None, jsonify(team).get_data(as_text=True)))

        return jsonify({"message":"Match request sent successfully."}), 200

    except Exception as e:
        return jsonify({"error":str(e)}), 500

    finally:
        cursor.close()
        connection.close()
