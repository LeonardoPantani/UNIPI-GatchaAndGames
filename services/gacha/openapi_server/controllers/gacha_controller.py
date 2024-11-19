import connexion
import uuid
import bcrypt
import random
import logging
import json

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util
from openapi_server.models.rarity_probability import RarityProbability  # noqa: E501

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError


def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200



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
            return {"error": "Gacha type not found."}, 404

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
        return gacha, 200

  
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def pull_gacha(pool_id):
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # Get pool probabilities and items
        cursor.execute(
            'SELECT probabilities, price FROM gacha_pools WHERE codename = %s',
            (pool_id,)
        )
        pool_result = cursor.fetchone()
        
        if not pool_result:
            return jsonify({"error": "Pool not found"}), 404

        probabilities = json.loads(pool_result[0])
        price = pool_result[1]

        # Check if user has enough credits (10)
        cursor.execute(
            'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
            (session['uuid'],)
        )
        result = cursor.fetchone()
        if not result or result[0] < price:
            return jsonify({"error": "Not enough credits"}), 403
        
        cursor.execute (
            'SELECT gacha_uuid FROM gacha_pools_items WHERE codename = %s',
            (pool_id,)
        )
        
        pullable_gachas = cursor.fetchall()
        
        # Determine rarity based on probabilities
        rarity_roll = random.random()
        selected_rarity = None
        cumulative_prob = 0
        
        for rarity, prob in probabilities.items():
            cumulative_prob += prob
            if rarity_roll <= cumulative_prob:
                selected_rarity = rarity.upper()
                break

        # Get random item of selected rarity
        # Generate placeholders for UUIDs dynamically
        placeholders = ','.join(['%s' for _ in pullable_gachas])

        # Define the query with the dynamically generated placeholders
        query = f'''
        SELECT BIN_TO_UUID(uuid), name, stat_power, stat_speed, 
            stat_durability, stat_precision, stat_range, stat_potential
        FROM gachas_types 
        WHERE uuid IN ({placeholders}) AND rarity = %s
        '''
        print(selected_rarity)
        # Extract only the first elements of each tuple from pullable_gachas for the UUIDs
        uuid_values = [item[0] for item in pullable_gachas]
        print(query)
        # Execute the query, passing UUID values and selected_rarity
        cursor.execute(query, uuid_values + [selected_rarity])
        items = cursor.fetchall()
        print(items)
        if not items:
            return jsonify({"error": "No items found in pool"}), 500
            
        selected_item = random.choice(items)
        
        # Deduct credits
        cursor.execute(
            'UPDATE profiles SET currency = currency - 10 WHERE uuid = UUID_TO_BIN(%s)',
            (session['uuid'],)
        )

        # Add to inventory
        # Add to inventory with new UUID
        new_item_uuid = str(uuid.uuid4())  

        cursor.execute(
        'INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, owners_no, currency_spent) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s)',
        (new_item_uuid, session['uuid'], selected_item[0], 0, 10)
        )

        connection.commit()

        # Return complete Gacha object
        gacha = Gacha(
            gacha_uuid=selected_item[0],
            name=selected_item[1],
            rarity=selected_rarity.lower(),
            attributes={
                "power": chr(ord('A') + 5 - max(1, min(5, selected_item[2] // 20))),
                "speed": chr(ord('A') + 5 - max(1, min(5, selected_item[3] // 20))),
                "durability": chr(ord('A') + 5 - max(1, min(5, selected_item[4] // 20))),
                "precision": chr(ord('A') + 5 - max(1, min(5, selected_item[5] // 20))),
                "range": chr(ord('A') + 5 - max(1, min(5, selected_item[6] // 20))),
                "potential": chr(ord('A') + 5 - max(1, min(5, selected_item[7] // 20)))
            }
        )

        return gacha
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_pool_info():  # noqa: E501
    cursor = None
    conn = None
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Query pools and their items
        cursor.execute('''
            SELECT 
                gp.codename,
                gp.public_name,
                gp.probabilities,
                gp.price,
                GROUP_CONCAT(BIN_TO_UUID(gpi.gacha_uuid)) as gacha_uuids
            FROM gacha_pools gp
            LEFT JOIN gacha_pools_items gpi ON gp.codename = gpi.codename
            GROUP BY gp.codename
        ''')
        
        results = cursor.fetchall()
        pools = []

        if not results:
            return jsonify({"error": "No pools found"}), 404
        
        for result in results:
            # Parse JSON strings from database
            probabilities = json.loads(result[2])
            gacha_uuids = result[4].split(',') if result[4] else []
            
            # Create RarityProbability object
            rarity_prob = RarityProbability(
                common_probability=probabilities.get('common', 0.5),
                rare_probability=probabilities.get('rare', 0.3),
                epic_probability=probabilities.get('epic', 0.15),
                legendary_probability=probabilities.get('legendary', 0.05)
            )

            # Query gacha details
            if gacha_uuids:
                placeholders = ','.join(['UUID_TO_BIN(%s)' for _ in gacha_uuids])
                cursor.execute(f'''
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
                    WHERE uuid IN ({placeholders})
                ''', gacha_uuids)
                
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
            else:
                items = []
            
            # Create Pool object
            pool = Pool(
                id=result[0],
                name=result[1],
                probabilities=rarity_prob,
                items=items
            )
            pools.append(pool)
            
        return jsonify(pools), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

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