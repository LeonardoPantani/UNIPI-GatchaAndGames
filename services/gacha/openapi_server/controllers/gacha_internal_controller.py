import connexion
from typing import Dict
from typing import Tuple
from typing import Union
import requests

from openapi_server.models.exists_gacha200_response import ExistsGacha200Response  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_rarity_by_uuid200_response import GetRarityByUuid200Response  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.gacha_attributes import GachaAttributes  # noqa: E501
from openapi_server import util
from openapi_server import util
from mysql.connector.errors import (
    OperationalError, DataError, DatabaseError, IntegrityError,
    InterfaceError, InternalError, ProgrammingError
)


from flask import session, jsonify

from openapi_server.helpers.db import get_db
from pybreaker import CircuitBreaker, CircuitBreakerError

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])

def create_gacha(gacha=None, session=None):  # noqa: E501
    """Creates gacha requested.
    
    :param gacha: Gacha object
    :type gacha: dict | bytes
    :param session: Session cookie
    :type session: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not connexion.request.is_json:
        return "", 400

    try:
        @circuit_breaker
        def insert_gacha():
            connection = get_db()
            cursor = connection.cursor()
            
            gacha_data = Gacha.from_dict(connexion.request.get_json())
            
            query = """
            INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, 
                                    stat_durability, stat_precision, stat_range, 
                                    stat_potential, rarity, release_date)
            VALUES (UUID_TO_BIN(%s), %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            # Convert letter grades back to numbers (A=100, B=80, etc)
            stats = {
                'power': (ord('F') - ord(gacha_data.attributes.power)) * 20,
                'speed': (ord('F') - ord(gacha_data.attributes.speed)) * 20,
                'durability': (ord('F') - ord(gacha_data.attributes.durability)) * 20,
                'precision': (ord('F') - ord(gacha_data.attributes.precision)) * 20,
                'range': (ord('F') - ord(gacha_data.attributes.range)) * 20,
                'potential': (ord('F') - ord(gacha_data.attributes.potential)) * 20
            }
            
            cursor.execute(query, (
                gacha_data.gacha_uuid,
                gacha_data.name,
                stats['power'],
                stats['speed'],
                stats['durability'],
                stats['precision'],
                stats['range'],
                stats['potential'],
                gacha_data.rarity
            ))
            
            connection.commit()
            cursor.close()
            return "", 201

        return insert_gacha()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def create_pool(pool=None, session=None):  # noqa: E501
    """Creates pool requested.

    :param pool: Pool object to create
    :type pool: dict | bytes
    :param session: Session cookie
    :type session: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not connexion.request.is_json:
        return "", 400

    try:
        pool_data = Pool.from_dict(connexion.request.get_json())

        @circuit_breaker
        def insert_pool():
            connection = get_db()
            cursor = connection.cursor()

            # Insert pool into gacha_pools table
            query = """
                INSERT INTO gacha_pools 
                (codename, public_name, probability_common, probability_rare, 
                probability_epic, probability_legendary, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                pool_data.codename,
                pool_data.public_name,
                pool_data.probability_common,
                pool_data.probability_rare,
                pool_data.probability_epic,
                pool_data.probability_legendary,
                pool_data.price
            ))

            # Insert pool items into gacha_pools_items table
            if pool_data.items:
                items_query = "INSERT INTO gacha_pools_items (codename, gacha_uuid) VALUES (%s, UUID_TO_BIN(%s))"
                for item_uuid in pool_data.items:
                    cursor.execute(items_query, (pool_data.codename, item_uuid))

            connection.commit()
            cursor.close()
            return "", 201

        return insert_pool()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_gacha(session=None, uuid=None):  # noqa: E501
    """Deletes requested gacha, also from pool item list.

    :param session: Session cookie
    :type session: str
    :param uuid: UUID of the gacha to delete
    :type uuid: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def delete_gacha_from_db():
            connection = get_db()
            cursor = connection.cursor()

            # First check if gacha exists
            check_query = "SELECT COUNT(*) FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(check_query, (uuid,))
            if cursor.fetchone()[0] == 0:
                cursor.close()
                return "", 404

            # Delete from gacha_pools_items first (foreign key)
            delete_from_pools = "DELETE FROM gacha_pools_items WHERE gacha_uuid = UUID_TO_BIN(%s)"
            cursor.execute(delete_from_pools, (uuid,))
            
            # Delete from gachas_types
            delete_query = "DELETE FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(delete_query, (uuid,))

            connection.commit()
            cursor.close()
            return "", 200

        return delete_gacha_from_db()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_pool(session=None, codename=None):  # noqa: E501
    """Deletes requested pool.

    :param session: Session cookie
    :type session: str
    :param codename: Codename of the pool to delete
    :type codename: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not codename:
        return "", 400

    try:
        @circuit_breaker
        def delete_pool_from_db():
            connection = get_db()
            cursor = connection.cursor()

            # First check if pool exists
            check_query = "SELECT COUNT(*) FROM gacha_pools WHERE codename = %s"
            cursor.execute(check_query, (codename,))
            if cursor.fetchone()[0] == 0:
                cursor.close()
                return "", 404

            # Delete from gacha_pools_items first (foreign key)
            delete_from_items = "DELETE FROM gacha_pools_items WHERE codename = %s"
            cursor.execute(delete_from_items, (codename,))
            
            # Delete from gacha_pools
            delete_query = "DELETE FROM gacha_pools WHERE codename = %s"
            cursor.execute(delete_query, (codename,))

            connection.commit()
            cursor.close()
            return "", 200

        return delete_pool_from_db()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_gacha(session=None, uuid=None):  # noqa: E501
    """Returns true if a gacha exists, false otherwise.

    :param session: Session cookie
    :type session: str
    :param uuid: Gacha UUID
    :type uuid: str
    :rtype: Union[ExistsGacha200Response, Tuple[ExistsGacha200Response, int], Tuple[ExistsGacha200Response, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def check_gacha_exists():
            connection = get_db()
            cursor = connection.cursor()
            
            query = "SELECT COUNT(*) FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()[0] > 0
            
            cursor.close()
            return jsonify({"exists": result}), 200

        return check_gacha_exists()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_pool(session=None, uuid=None):  # noqa: E501  #note: uuid is actually the codename
    """Returns true if a pool exists, false otherwise.

    :param session: Session cookie
    :type session: str
    :param codename: Pool codename
    :type codename: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def check_pool_exists():
            connection = get_db()
            cursor = connection.cursor()
            
            query = "SELECT COUNT(*) FROM gacha_pools WHERE codename = %s"
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()[0] > 0
            
            cursor.close()
            return jsonify({"exists": result}), 200

        return check_pool_exists()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_gacha(session=None, uuid=None):  # noqa: E501
    """Returns the gacha object by gacha uuid.

    :param session: Session cookie
    :type session: str
    :param uuid: UUID of the gacha
    :type uuid: str
    :rtype: Union[Gacha, Tuple[Gacha, int], Tuple[Gacha, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def get_gacha_from_db():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
                SELECT BIN_TO_UUID(uuid), name, rarity, 
                       stat_power, stat_speed, stat_durability, stat_precision, 
                       stat_range, stat_potential
                FROM gachas_types 
                WHERE uuid = UUID_TO_BIN(%s)
            """
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return "", 404

            gacha_data = {
                "gacha_uuid": result[0],
                "name": result[1],
                "rarity": result[2],
                "attributes": {
                    "power": str(result[3]),
                    "speed": str(result[4]),
                    "durability": str(result[5]),
                    "precision": str(result[6]),
                    "range": str(result[7]),
                    "potential": str(result[8])
                }
            }

            cursor.close()
            return jsonify(gacha_data), 200

        return get_gacha_from_db()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_pool(session=None, uuid=None):  # noqa: E501
    """get_pool

    Returns true if a pool exists, false otherwise. # noqa: E501

    :param session: 
    :type session: str
    :param uuid: 
    :type uuid: str

    :rtype: Union[Pool, Tuple[Pool, int], Tuple[Pool, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_rarity_by_uuid(session=None, uuid=None):  # noqa: E501
    """Returns the rarity of a gacha.

    :param session: Session cookie
    :type session: str
    :param uuid: UUID of the gacha
    :type uuid: str
    :rtype: Union[GetRarityByUuid200Response, Tuple[GetRarityByUuid200Response, int], Tuple[GetRarityByUuid200Response, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:
        @circuit_breaker
        def get_rarity_from_db():
            connection = get_db()
            cursor = connection.cursor()
            
            query = "SELECT rarity FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                return "", 404

            cursor.close()
            return jsonify({"rarity": result[0]}), 200

        return get_rarity_from_db()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def list_gachas(request_body, session=None, not_owned=None):  # noqa: E501
    """list_gachas

    Returns list of gachas (not) owned by the user. # noqa: E501

    :param request_body: 
    :type request_body: List[str]
    :param session: 
    :type session: str
    :param not_owned: 
    :type not_owned: bool

    :rtype: Union[List[Gacha], Tuple[List[Gacha], int], Tuple[List[Gacha], int, Dict[str, str]]
    """
    return 'do some magic!'


def list_pools(session=None):  # noqa: E501
    """list_pools

    Returns list of pools. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]
    """
    return 'do some magic!'


def update_gacha(session=None, gacha=None):  # noqa: E501
    """update_gacha

    Updates a gacha. # noqa: E501

    :param session: 
    :type session: str
    :param gacha: 
    :type gacha: dict | bytes

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool, session=None):  # noqa: E501
    """update_pool

    Updates a pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
