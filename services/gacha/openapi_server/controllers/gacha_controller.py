import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import current_app,session

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util
from openapi_server.models.rarity_probability import RarityProbability  # noqa: E501
import json
import random


def get_gacha_info(gacha_uuid):  # noqa: E501
    """Shows infos on a gacha.

    Returns infos on a gacha. # noqa: E501
    """
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

    except Exception as e:
        return {"error": str(e)}, 500
        
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


def get_pool_info():  # noqa: E501
    """Lists available pools.

    Returns a list of available gacha pools. # noqa: E501

    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
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


def pull_gacha(pool_id):  # noqa: E501
    """Pull a random gacha from a specific pool.
    
    Allows a player to pull a random gacha item from a specified pool. Consumes in-game currency. # noqa: E501

    :param session: Session cookie for authentication
    :type session: str
    :param pool_id: Pool to pull from 
    :type pool_id: str
    :param session: 
    :type session: str

    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]
    """
    cursor = None
    conn = None
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Get username from session
        username = session.get('username')
        if not username:
            return {"error": "Not logged in"}, 403

        # Get user UUID from profiles
        cursor.execute('''
            SELECT BIN_TO_UUID(uuid) 
            FROM profiles 
            WHERE username = %s
        ''', (username,))
        
        result = cursor.fetchone()
        if not result:
            return {"error": "User not found"}, 404
        user_uuid = result[0]

        # Get pool info and verify it exists
        cursor.execute('SELECT probabilities, items FROM gacha_pools WHERE codename = %s', (pool_id,))
        pool = cursor.fetchone()
        if not pool:
            return {"error": "Pool not found"}, 404

        # Parse pool data
        probabilities = json.loads(pool[0])
        items = json.loads(pool[1])

        # Check if user has enough currency (100 credits per pull)
        cursor.execute('SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)', (user_uuid,))
        currency = cursor.fetchone()[0]
        if currency < 100:
            return {"error": "Insufficient funds"}, 403

        # Calculate pull based on probabilities
        roll = random.random()
        rarity = None
        if roll < probabilities['legendary']:
            rarity = 'LEGENDARY'
        elif roll < probabilities['legendary'] + probabilities['epic']:
            rarity = 'EPIC'
        elif roll < probabilities['legendary'] + probabilities['epic'] + probabilities['rare']:
            rarity = 'RARE'
        else:
            rarity = 'COMMON'

        # Get random gacha of selected rarity from pool
        cursor.execute('''
            SELECT BIN_TO_UUID(uuid), name, stat_power, stat_speed, stat_durability, 
                   stat_precision, stat_range, stat_potential
            FROM gachas_types 
            WHERE name IN %s AND rarity = %s
        ''', (tuple(items), rarity))
        
        possible_pulls = cursor.fetchall()
        if not possible_pulls:
            return {"error": "No items found in pool"}, 500
            
        pulled = random.choice(possible_pulls)

        # Create new inventory item
        cursor.execute('SELECT UUID()')
        item_uuid = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, owners_no, currency_spent)
            VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), 1, 100)
        ''', (item_uuid, user_uuid, pulled[0]))

        # Deduct currency and log transaction
        cursor.execute('''
            UPDATE profiles SET currency = currency - 100 
            WHERE uuid = UUID_TO_BIN(%s)
        ''', (user_uuid,))

        cursor.execute('''
            INSERT INTO ingame_transactions (user_uuid, credits, transaction_type)
            VALUES (UUID_TO_BIN(%s), -100, 'gacha_pull')
        ''', (user_uuid,))

        conn.commit()

        # Return pulled gacha
        return Gacha(
            gacha_uuid=pulled[0],
            name=pulled[1],
            rarity=rarity.lower(),
            attributes={
                "power": chr(ord('A') + 5 - max(1, min(5, pulled[2] // 20))),
                "speed": chr(ord('A') + 5 - max(1, min(5, pulled[3] // 20))),
                "durability": chr(ord('A') + 5 - max(1, min(5, pulled[4] // 20))),
                "precision": chr(ord('A') + 5 - max(1, min(5, pulled[5] // 20))),
                "range": chr(ord('A') + 5 - max(1, min(5, pulled[6] // 20))),
                "potential": chr(ord('A') + 5 - max(1, min(5, pulled[7] // 20)))
            }
        )

    except Exception as e:
        if conn:
            conn.rollback()
        return {"error": str(e)}, 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
