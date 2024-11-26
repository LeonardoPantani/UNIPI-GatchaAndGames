import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha
from openapi_server.models.ban_user_profile_request import BanUserProfileRequest
from openapi_server.models.get_currency200_response import GetCurrency200Response
from openapi_server.models.get_gacha_info_request import GetGachaInfoRequest
from openapi_server.models.get_gacha_list_request import GetGachaListRequest
from openapi_server.models.give_item_request import GiveItemRequest
from openapi_server.models.pool import Pool
from openapi_server import util
from openapi_server.helpers.functions import stats_number_to_letter
from openapi_server.helpers.logging import send_log

from flask import jsonify, g
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.db import get_db
import logging
from datetime import datetime

# Circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(
    fail_max=3,
    reset_timeout=5,
    exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError]
)

def get_gacha_info(get_gacha_info_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_gacha_info_request = GetGachaInfoRequest.from_dict(connexion.request.get_json())
    gacha_uuid = get_gacha_info_request.gacha_uuid

    try:
        @circuit_breaker
        def make_request_to_db():
            db = get_db()
            cursor = db.cursor(dictionary=True)
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
            return cursor.fetchone()

        gacha_data = make_request_to_db()
        if not gacha_data:
            return "", 404
        
        print(gacha_data)
        return "",200

        # Create a Gacha object with the retrieved data
        gacha_attributes = { 
            "power": gacha_data['stat_power'],
            "speed": gacha_data['stat_speed'],
            "durability": gacha_data['stat_durability'],
            "precision": gacha_data['stat_precision'],
            "range": gacha_data['stat_range'],
            "potential": gacha_data['stat_potential']
        }

        converted = stats_number_to_letter(gacha_attributes)

        gacha = Gacha(
            gacha_uuid=gacha_data['gacha_uuid'],
            name=gacha_data['name'], 
            stat_power=converted["power"],
            stat_speed=converted["speed"],
            stat_durability=converted["durability"],
            stat_precision=converted["precision"],
            stat_range=converted["range"],
            stat_potential=converted["potential"],
            rarity=gacha_data['rarity']
        )
        return jsonify(gacha), 200
    
    except OperationalError:
        logging.error(f"Query [{gacha_uuid}]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error(f"Query [{gacha_uuid}]: Programming error.")
        return "", 500
    except IntegrityError:
        logging.error(f"Query [{gacha_uuid}]: Integrity error.")
        return "", 500
    except DataError:
        logging.error(f"Query [{gacha_uuid}]: Data error.")
        return "", 500
    except InternalError:
        logging.error(f"Query [{gacha_uuid}]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error(f"Query [{gacha_uuid}]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error(f"Query [{gacha_uuid}]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_gacha_list(get_gacha_list_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    get_gacha_list_request = GetGachaListRequest.from_dict(connexion.request.get_json())
    
    user_uuid = get_gacha_list_request.user_uuid
    not_owned = get_gacha_list_request.owned_filter

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()

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

            return cursor.fetchall()
        
        gacha_list = make_request_to_db()

        if not gacha_list:
            return "", 404

        gachas = []
        for result in gacha_list:
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
        return jsonify(gachas), 200

    except OperationalError:
        logging.error("Query ["+ user_uuid +"]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ user_uuid +"]: Programming error.")
        return "", 400
    except IntegrityError:
        logging.error("Query ["+ user_uuid +"]: Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid +"]: Data error.")
        return "", 500
    except InternalError:
        logging.error("Query ["+ user_uuid +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ user_uuid +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ user_uuid +"]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
     

def get_pool_info(body):
    if body is None:
        return "", 400
    
    pool_codename = body

    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT codename, public_name, probabilities, price FROM gacha_pools WHERE codename = %s',
                (pool_codename,)
            )
            pool_data = cursor.fetchone()

            if not pool_data:
                return "", "", 404

            cursor.execute(
                'SELECT BIN_TO_UUID(gt.uuid), gt.name, gt.rarity, gt.stat_power, gt.stat_speed, gt.stat_durability, gt.stat_precision, gt.stat_range, gt.stat_potential FROM gacha_pools_items gpi JOIN gachas_types gt ON gpi.gacha_uuid = gt.uuid WHERE gpi.codename = %s',
                (pool_codename,)
            )
            pool_items = cursor.fetchall()

            return pool_data, pool_items, 200

        pool, items, code = make_request_to_db()

        if code != 200:
            return "", code

        gachas = []
        for row in items:
            gacha = Gacha(
            gacha_uuid=row[0],
            name=row[1], 
            attributes={
                "power": chr(ord('A') + 5 - max(1, min(5, row[3] // 20))),
                "speed": chr(ord('A') + 5 - max(1, min(5, row[4] // 20))),
                "durability": chr(ord('A') + 5 - max(1, min(5, row[5] // 20))),
                "precision": chr(ord('A') + 5 - max(1, min(5, row[6] // 20))),
                "range": chr(ord('A') + 5 - max(1, min(5, row[7] // 20))),
                "potential": chr(ord('A') + 5 - max(1, min(5, row[8] // 20)))
            },
            rarity=row[2]
            )
            gachas.append(gacha) 

        payload = {
            "price": pool[3],
            "public_name": pool[1],
            "codename": pool[0],
            "probabilities": pool[2],
            "items": gachas
        }
        return jsonify(payload), 200

    except OperationalError:
        logging.error("Query ["+ pool_codename +"]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query ["+ pool_codename +"]: Programming error.")
        return "", 400
    except IntegrityError:
        logging.error("Query ["+ pool_codename +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ pool_codename +"]: Data error.")
        return "", 400
    except InternalError:
        logging.error("Query ["+ pool_codename +"]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query ["+ pool_codename +"]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query ["+ pool_codename +"]: Database error.")
        return "", 401
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def get_pools_list():   

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT codename, public_name, probabilities, price FROM gacha_pools',
            )
            pool_data = cursor.fetchall()
            
            if not pool_data: # rimuovere codice 404, restituire lista vuota
                return "", 404

            return pool_data, 200

        pool_list, code = make_request_to_db()

        if code != 200:
            return "", code
        pools = []
        for pool in pool_list:

            def make_request_to_db():
                connection = get_db()
                cursor = connection.cursor()
                cursor.execute(
                    'SELECT BIN_TO_UUID(gt.uuid), gt.name, gt.rarity, gt.stat_power, gt.stat_speed, gt.stat_durability, gt.stat_precision, gt.stat_range, gt.stat_potential FROM gacha_pools_items gpi JOIN gachas_types gt ON gpi.gacha_uuid = gt.uuid WHERE gpi.codename = %s',
                     (pool[0],)
                )
                item_list = cursor.fetchall()
                return item_list
            
            item_list = make_request_to_db()
            gachas = []
            for row in item_list:
                gacha = Gacha(
                gacha_uuid=row[0],
                name=row[1], 
                attributes={
                    "power": chr(ord('A') + 5 - max(1, min(5, row[3] // 20))),
                    "speed": chr(ord('A') + 5 - max(1, min(5, row[4] // 20))),
                    "durability": chr(ord('A') + 5 - max(1, min(5, row[5] // 20))),
                    "precision": chr(ord('A') + 5 - max(1, min(5, row[6] // 20))),
                    "range": chr(ord('A') + 5 - max(1, min(5, row[7] // 20))),
                    "potential": chr(ord('A') + 5 - max(1, min(5, row[8] // 20)))
                },
                rarity=row[2]
                )
                gachas.append(gacha) 
            payload = {
                "price": pool[3],
                "name": pool[1],
                "id": pool[0],
                "probabilities": pool[2],
                "items": gachas
            }
            pools.append(payload)

        return jsonify(pools), 200

    except OperationalError:
        logging.error("Query : Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query : Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query : Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query : Data error.")
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


def get_currency(ban_user_profile_request=None):
    if not connexion.request.is_json:
        return "", 400
        
    get_user_currency_request = BanUserProfileRequest.from_dict(connexion.request.get_json())

    user_uuid = get_user_currency_request.user_uuid
        

    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
                (user_uuid,)
            )

            result = cursor.fetchone()
            return result

        currency = make_request_to_db()
        payload = {
            "currency": currency[0]
        }

        return jsonify(payload), 200    

    except OperationalError:
        logging.error("Query : Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query : Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query : Integrity error.")
        return "", 500
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query : Data error.")
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


def give_item(give_item_request=None):
    if not connexion.request.is_json:
        return "", 400
    
    give_item_request = GiveItemRequest.from_dict(connexion.request.get_json())

    user_uuid = give_item_request.owner_uuid
    item_uuid = give_item_request.item_uuid
    stand_uuid = give_item_request.stand_uuid
    price_paid = give_item_request.price_paid

    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE profiles SET currency = currency - %s WHERE uuid = UUID_TO_BIN(%s)',
                (price_paid, user_uuid)
            )

            cursor.execute( 
                'INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, owners_no, currency_spent) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), %s, %s)',
                (item_uuid, user_uuid, stand_uuid, 1, price_paid)
            )

            connection.commit()
            return

        make_request_to_db()

        return "", 201

    except OperationalError:
        logging.error("Query : Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query : Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query : Integrity error.")
        if connection:
            connection.close()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query : Data error.")
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