import connexion
import uuid
import bcrypt
import random
import logging

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util
from openapi_server.models.rarity_probability import RarityProbability  # noqa: E501

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
gacha_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


@gacha_circuit_breaker
def get_gacha_info(gacha_uuid):  # noqa: E501
    cursor = None
    conn = None
    try:
        # Get database connection from Flask current_app
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Query the gacha info from the database
        cursor.execute('''
            SELECT 
                BIN_TO_UUID(uuid) as gacha_uuid,
                name,
                LOWER(rarity) as rarity,
                stat_power,
                stat_speed,
                stat_durability,
                stat_precision,
                stat_range,
                stat_potential
            FROM gachas_types 
            WHERE uuid = UUID_TO_BIN(%s)
        ''', (gacha_uuid,))
        
        result = cursor.fetchone()
        if not result:
            return {"error": "Gacha not found"}, 404

        # Create a Gacha object with the retrieved data
        gacha = Gacha(
            gacha_uuid=result[0],
            name=result[1], 
            rarity=result[2],
            attributes={
                "power": chr(ord('A') + 5 - max(1, min(5, result[3] // 20))),
                "speed": chr(ord('A') + 5 - max(1, min(5, result[4] // 20))),
                "durability": chr(ord('A') + 5 - max(1, min(5, result[5] // 20))),
                "precision": chr(ord('A') + 5 - max(1, min(5, result[6] // 20))),
                "range": chr(ord('A') + 5 - max(1, min(5, result[7] // 20))),
                "potential": chr(ord('A') + 5 - max(1, min(5, result[8] // 20)))
            }
        )
        return gacha

    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return {"error": "Service unavailable. Please try again later."}, 503
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@gacha_circuit_breaker
def pull_gacha():  # noqa: E501
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    user_uuid = session['uuid']

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    try:
        connection = mysql.connect()
        cursor = connection.cursor()

        # Check if user has enough credits for a gacha roll
        cursor.execute(
            'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
            (user_uuid,)
        )
        result = cursor.fetchone()

        if not result or result[0] < 10:  # Assuming 10 credits are needed for a roll
            return jsonify({"error": "Not enough credits for a gacha roll."}), 400

        # Deduct credits for the gacha roll
        cursor.execute(
            'UPDATE profiles SET currency = currency - 10 WHERE uuid = UUID_TO_BIN(%s)',
            (user_uuid,)
        )

        # Simulate gacha roll (for simplicity, just generate a random UUID as the prize)
        prize_uuid = str(uuid.uuid4())

        # Insert the prize into the user's inventory
        cursor.execute(
            'INSERT INTO inventories (owner_uuid, item_uuid) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s))',
            (user_uuid, prize_uuid)
        )

        connection.commit()

        return jsonify({"message": "Gacha roll successful", "prize": prize_uuid}), 200
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except Exception as e:
        logging.error(f"Error while performing gacha roll: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@gacha_circuit_breaker
def get_pool_info():  # noqa: E501
    cursor = None
    conn = None
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Query all pools from gacha_pools table
        cursor.execute('''
            SELECT 
                codename,
                public_name,
                probabilities,
                items
            FROM gacha_pools
        ''')
        
        results = cursor.fetchall()
        pools = []
        
        for result in results:
            # Parse JSON strings from database
            probabilities = json.loads(result[2])
            items_list = json.loads(result[3])
            
            # Create RarityProbability object
            rarity_prob = RarityProbability(
                common_probability=probabilities.get('common', 0.5),
                rare_probability=probabilities.get('rare', 0.3),
                epic_probability=probabilities.get('epic', 0.15),
                legendary_probability=probabilities.get('legendary', 0.05)
            )
            
            # Get gacha items for this pool
            cursor.execute('''
                SELECT 
                    BIN_TO_UUID(uuid) as gacha_uuid,
                    name,
                    LOWER(rarity) as rarity,
                    stat_power,
                    stat_speed,
                    stat_durability,
                    stat_precision,
                    stat_range,
                    stat_potential
                FROM gachas_types 
                WHERE name IN %s
            ''', (tuple(items_list),))
            
            items = []
            for item in cursor.fetchall():
                items.append(Gacha(
                    gacha_uuid=item[0],
                    name=item[1],
                    rarity=item[2],
                    attributes={
                        "power": chr(ord('A') + 5 - max(1, min(5, item[3] // 20))),
                        "speed": chr(ord('A') + 5 - max(1, min(5, item[4] // 20))),
                        "durability": chr(ord('A') + 5 - max(1, min(5, item[5] // 20))),
                        "precision": chr(ord('A') + 5 - max(1, min(5, item[6] // 20))),
                        "range": chr(ord('A') + 5 - max(1, min(5, item[7] // 20))),
                        "potential": chr(ord('A') + 5 - max(1, min(5, item[8] // 20)))
                    }
                ))
            
            # Create Pool object
            pool = Pool(
                id=result[0],
                name=result[1],
                probabilities=rarity_prob,
                items=items
            )
            pools.append(pool)
            
        return pools

    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@gacha_circuit_breaker
def get_gachas(not_owned=None):  # noqa: E501
    """Lists all gachas.
    
    Returns a list of all gachas. If not_owned is True, shows only unowned gachas.
    If not_owned is False, shows only owned gachas.
    """
    cursor = None
    conn = None
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Get user_uuid from session if filter is active
        user_uuid = None
        if not_owned is not None:  # If we need to filter by ownership
            username = session.get('username')
            if not username:
                return {"error": "Not logged in"}, 403
                
            cursor.execute('''
                SELECT BIN_TO_UUID(uuid) 
                FROM profiles 
                WHERE username = %s
            ''', (username,))
            result = cursor.fetchone()
            if not result:
                return {"error": "User not found"}, 404
            user_uuid = result[0]

        if user_uuid:
            if not_owned:  # Show unowned gachas
                cursor.execute('''
                    SELECT DISTINCT
                        BIN_TO_UUID(gt.uuid) as gacha_uuid,
                        gt.name,
                        LOWER(gt.rarity) as rarity,
                        gt.stat_power,
                        gt.stat_speed,
                        gt.stat_durability,
                        gt.stat_precision,
                        gt.stat_range,
                        gt.stat_potential
                    FROM gachas_types gt
                    WHERE NOT EXISTS (
                        SELECT 1 FROM inventories i 
                        WHERE i.stand_uuid = gt.uuid 
                        AND i.owner_uuid = UUID_TO_BIN(%s)
                    )
                ''', (user_uuid,))
            else:  # Show only owned gachas
                cursor.execute('''
                    SELECT DISTINCT
                        BIN_TO_UUID(gt.uuid) as gacha_uuid,
                        gt.name,
                        LOWER(gt.rarity) as rarity,
                        gt.stat_power,
                        gt.stat_speed,
                        gt.stat_durability,
                        gt.stat_precision,
                        gt.stat_range,
                        gt.stat_potential
                    FROM gachas_types gt
                    INNER JOIN inventories i ON 
                        i.stand_uuid = gt.uuid AND
                        i.owner_uuid = UUID_TO_BIN(%s)
                ''', (user_uuid,))
        else:  # Show all gachas when no filter
            cursor.execute('''
                SELECT
                    BIN_TO_UUID(uuid) as gacha_uuid,
                    name,
                    LOWER(rarity) as rarity,
                    stat_power,
                    stat_speed,
                    stat_durability,
                    stat_precision,
                    stat_range,
                    stat_potential
                FROM gachas_types
            ''')

        gachas = []
        for result in cursor.fetchall():
            gacha = Gacha(
                gacha_uuid=result[0],
                name=result[1],
                rarity=result[2],
                attributes={
                    "power": chr(ord('A') + 5 - max(1, min(5, result[3] // 20))),
                    "speed": chr(ord('A') + 5 - max(1, min(5, result[4] // 20))),
                    "durability": chr(ord('A') + 5 - max(1, min(5, result[5] // 20))),
                    "precision": chr(ord('A') + 5 - max(1, min(5, result[6] // 20))),
                    "range": chr(ord('A') + 5 - max(1, min(5, result[7] // 20))),
                    "potential": chr(ord('A') + 5 - max(1, min(5, result[8] // 20)))
                }
            )
            gachas.append(gacha)
        return gachas
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()