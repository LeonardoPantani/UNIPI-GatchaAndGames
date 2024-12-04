
import connexion
import requests
from flask import jsonify, session
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

from openapi_server import util
from openapi_server.helpers.db import get_db
from openapi_server.helpers.stats import map_grade_to_number, map_number_to_grade
from openapi_server.models.exists_gacha200_response import ExistsGacha200Response
from openapi_server.models.gacha import Gacha
from openapi_server.models.gacha_attributes import GachaAttributes
from openapi_server.models.get_rarity_by_uuid200_response import GetRarityByUuid200Response
from openapi_server.models.pool import Pool

circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=5,
    exclude=[
        requests.HTTPError,
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ],
)


def create_gacha(gacha=None, session=None):
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

            # Convert letter grades back to numbers
            stats = {
                "power": map_grade_to_number(gacha_data.attributes.power),
                "speed": map_grade_to_number(gacha_data.attributes.speed),
                "durability": map_grade_to_number(gacha_data.attributes.durability),
                "precision": map_grade_to_number(gacha_data.attributes.precision),
                "range": map_grade_to_number(gacha_data.attributes.range),
                "potential": map_grade_to_number(gacha_data.attributes.potential),
            }

            cursor.execute(
                query,
                (
                    gacha_data.gacha_uuid,
                    gacha_data.name,
                    stats["power"],
                    stats["speed"],
                    stats["durability"],
                    stats["precision"],
                    stats["range"],
                    stats["potential"],
                    gacha_data.rarity,
                ),
            )

            connection.commit()
            cursor.close()
            return "", 201

        return insert_gacha()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def create_pool(pool=None, session=None):
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

            # First check if pool with same codename exists
            check_pool_query = "SELECT COUNT(*) FROM gacha_pools WHERE codename = %s"
            cursor.execute(check_pool_query, (pool_data.codename,))
            if cursor.fetchone()[0] > 0:
                cursor.close()
                return "Pool with this codename already exists", 409  # Pool with this codename already exists

            # Verify if all items exist before proceeding
            if pool_data.items:
                check_query = """
                    SELECT COUNT(*) FROM gachas_types 
                    WHERE uuid IN ({})
                """.format(",".join(["UUID_TO_BIN(%s)" for _ in pool_data.items]))

                cursor.execute(check_query, pool_data.items)
                count = cursor.fetchone()[0]

                if count != len(pool_data.items):
                    cursor.close()
                    return "Some items don't exist", 400  # Some items don't exist

            # Insert pool into gacha_pools table
            query = """
                INSERT INTO gacha_pools 
                (codename, public_name, probability_common, probability_rare, 
                probability_epic, probability_legendary, price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (
                    pool_data.codename,
                    pool_data.public_name,
                    pool_data.probability_common,
                    pool_data.probability_rare,
                    pool_data.probability_epic,
                    pool_data.probability_legendary,
                    pool_data.price,
                ),
            )

            # Insert pool items into gacha_pools_items table
            if pool_data.items:
                items_query = "INSERT INTO gacha_pools_items (codename, gacha_uuid) VALUES (%s, UUID_TO_BIN(%s))"
                for item_uuid in pool_data.items:
                    cursor.execute(items_query, (pool_data.codename, item_uuid))

            connection.commit()
            cursor.close()
            return "", 201

        return insert_pool()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_gacha(session=None, uuid=None):
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

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_pool(session=None, codename=None):
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

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_gacha(session=None, uuid=None):
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

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_pool(session=None, uuid=None):  # note: uuid is actually the codename
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

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_gacha(session=None, uuid=None):
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
                    "power": map_number_to_grade(result[3]),
                    "speed": map_number_to_grade(result[4]),
                    "durability": map_number_to_grade(result[5]),
                    "precision": map_number_to_grade(result[6]),
                    "range": map_number_to_grade(result[7]),
                    "potential": map_number_to_grade(result[8]),
                },
            }

            cursor.close()
            return jsonify(gacha_data), 200

        return get_gacha_from_db()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_pool(session=None, uuid=None):  # note: uuid is actually the codename
    """Returns the pool object by pool codename.

    :param session: Session cookie
    :type session: str
    :param codename: Codename of the pool
    :type codename: str
    :rtype: Union[Pool, Tuple[Pool, int], Tuple[Pool, int, Dict[str, str]]]
    """
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def get_pool_from_db():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT codename, public_name, probability_common, probability_rare,
                       probability_epic, probability_legendary, price
                FROM gacha_pools 
                WHERE codename = %s
            """
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()

            if not result:
                cursor.close()
                return "", 404

            items_query = "SELECT BIN_TO_UUID(gacha_uuid) FROM gacha_pools_items WHERE codename = %s"
            cursor.execute(items_query, (uuid,))
            items = [str(item[0]) for item in cursor.fetchall()]

            pool_data = {
                "codename": result[0],
                "public_name": result[1],
                "probability_common": result[2],
                "probability_rare": result[3],
                "probability_epic": result[4],
                "probability_legendary": result[5],
                "price": result[6],
                "items": items,
            }

            cursor.close()
            return jsonify(pool_data), 200

        return get_pool_from_db()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_rarity_by_uuid(session=None, uuid=None):
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

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def list_gachas(requestBody=None, session=None, not_owned=None): #TODO
    """Returns a list of gachas by UUIDs."""
    if connexion.request.is_json:
        requestBody = connexion.request.get_json()
    
    try:
        if not requestBody:
            return "", 400
        
        @circuit_breaker
        def get_gachas_from_db():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT BIN_TO_UUID(uuid), name, rarity, 
                       stat_power, stat_speed, stat_durability, stat_precision, 
                       stat_range, stat_potential
                FROM gachas_types 
            """
            cursor.execute(query)
            results = cursor.fetchall()

            cursor.close()
            
            return results

        results = get_gachas_from_db()

        gachas = []
        for result in results:
            gacha = {
                "gacha_uuid": result[0],
                "name": result[1],
                "rarity": result[2],
                "attributes": {
                    "power": map_number_to_grade(result[3]),
                    "speed": map_number_to_grade(result[4]),
                    "durability": map_number_to_grade(result[5]),
                    "precision": map_number_to_grade(result[6]),
                    "range": map_number_to_grade(result[7]),
                    "potential": map_number_to_grade(result[8]),
                },
            }
            if not_owned and result[0] not in requestBody:
                gachas.append(gacha)
            elif not not_owned and result[0] in requestBody:
                gachas.append(gacha)
        return jsonify(gachas), 200

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def list_pools(session=None):
    """Returns list of pools.

    :param session: Session cookie
    :type session: str
    :rtype: Union[List[Pool], Tuple[List[Pool], int], Tuple[List[Pool], int, Dict[str, str]]]
    """

    try:

        @circuit_breaker
        def get_pools_from_db():
            connection = get_db()
            cursor = connection.cursor()

            query = """
                SELECT codename, public_name, probability_common, probability_rare,
                       probability_epic, probability_legendary, price
                FROM gacha_pools
            """
            cursor.execute(query)
            results = cursor.fetchall()

            pools = []
            for result in results:
                codename = result[0]

                items_query = "SELECT BIN_TO_UUID(gacha_uuid) FROM gacha_pools_items WHERE codename = %s"
                cursor.execute(items_query, (codename,))
                items = [item[0] for item in cursor.fetchall()]

                pool = {
                    "codename": codename,
                    "public_name": result[1],
                    "probability_common": result[2],
                    "probability_rare": result[3],
                    "probability_epic": result[4],
                    "probability_legendary": result[5],
                    "price": result[6],
                    "items": items,
                }
                pools.append(pool)

            cursor.close()
            return jsonify(pools), 200

        return get_pools_from_db()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def update_gacha(gacha=None, session=None):
    if not connexion.request.is_json:
        return "", 400

    try:
        gacha_data = connexion.request.get_json()
        if not gacha_data:
            return "", 400

        # Check rarity value before proceeding
        valid_rarities = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
        if gacha_data["rarity"].upper() not in valid_rarities:
            return "", 400

        gacha_object = Gacha.from_dict(gacha_data)

        @circuit_breaker
        def update_gacha_in_db():
            connection = get_db()
            cursor = connection.cursor()

            # First check if gacha exists and get current values
            check_query = """
                SELECT name, rarity, stat_power, stat_speed, stat_durability,
                       stat_precision, stat_range, stat_potential
                FROM gachas_types 
                WHERE uuid = UUID_TO_BIN(%s)
            """
            cursor.execute(check_query, (gacha_object.gacha_uuid,))
            current = cursor.fetchone()

            if not current:
                cursor.close()
                return "", 404

            # Check if values are the same
            if (
                current[0] == gacha_object.name
                and current[1].upper() == gacha_object.rarity.upper()
                and map_grade_to_number(gacha_object.attributes.power) == current[2]
                and map_grade_to_number(gacha_object.attributes.speed) == current[3]
                and map_grade_to_number(gacha_object.attributes.durability) == current[4]
                and map_grade_to_number(gacha_object.attributes.precision) == current[5]
                and map_grade_to_number(gacha_object.attributes.range) == current[6]
                and map_grade_to_number(gacha_object.attributes.potential) == current[7]
            ):
                cursor.close()
                return "", 304

            query = """
                UPDATE gachas_types 
                SET name = %s, rarity = UPPER(%s),
                    stat_power = %s, stat_speed = %s, stat_durability = %s,
                    stat_precision = %s, stat_range = %s, stat_potential = %s
                WHERE uuid = UUID_TO_BIN(%s)
            """

            cursor.execute(
                query,
                (
                    gacha_object.name,
                    gacha_object.rarity,
                    map_grade_to_number(gacha_object.attributes.power),
                    map_grade_to_number(gacha_object.attributes.speed),
                    map_grade_to_number(gacha_object.attributes.durability),
                    map_grade_to_number(gacha_object.attributes.precision),
                    map_grade_to_number(gacha_object.attributes.range),
                    map_grade_to_number(gacha_object.attributes.potential),
                    gacha_object.gacha_uuid,
                ),
            )

            connection.commit()
            cursor.close()
            return "", 200

        return update_gacha_in_db()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def update_pool(pool=None, session=None):
    """Updates a pool.

    :param pool: Pool object to update
    :type pool: dict | bytes
    :param session: Session cookie
    :type session: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not connexion.request.is_json:
        return "", 400

    try:
        pool_data = connexion.request.get_json()
        if not pool_data:
            return "", 400

        pool_object = Pool.from_dict(pool_data)

        # Validate probabilities sum to 1
        total_prob = (
            pool_object.probability_common
            + pool_object.probability_rare
            + pool_object.probability_epic
            + pool_object.probability_legendary
        )
        if not 0.99 <= total_prob <= 1.01:  # Allow for small floating point errors
            return "", 400

        # Validate price is positive
        if pool_object.price <= 0:
            return "", 400

        @circuit_breaker
        def update_pool_in_db():
            connection = get_db()
            cursor = connection.cursor()

            # TODO risolvere possibile sql injection
            # Check if all items exist
            if pool_object.items:
                placeholders = ",".join(["UUID_TO_BIN(%s)" for _ in pool_object.items])
                items_check = f"SELECT COUNT(*) FROM gachas_types WHERE uuid IN ({placeholders})"
                cursor.execute(items_check, pool_object.items)
                if cursor.fetchone()[0] != len(pool_object.items):
                    cursor.close()
                    return "", 400  # At least one item doesn't exist

            #  check if pool exists and get current values
            check_query = """
                SELECT codename, public_name, probability_common, probability_rare,
                       probability_epic, probability_legendary, price
                FROM gacha_pools 
                WHERE codename = %s
            """
            cursor.execute(check_query, (pool_object.codename,))
            current = cursor.fetchone()

            if not current:
                cursor.close()
                return "", 404

            # Check if values are the same
            if (
                current[0] == pool_object.codename
                and current[1] == pool_object.public_name
                and float(current[2]) == pool_object.probability_common
                and float(current[3]) == pool_object.probability_rare
                and float(current[4]) == pool_object.probability_epic
                and float(current[5]) == pool_object.probability_legendary
                and int(current[6]) == pool_object.price
            ):
                cursor.close()
                return "", 304

            # Update pool data
            query = """
                UPDATE gacha_pools 
                SET public_name = %s,
                    probability_common = %s,
                    probability_rare = %s,
                    probability_epic = %s,
                    probability_legendary = %s,
                    price = %s
                WHERE codename = %s
            """
            cursor.execute(
                query,
                (
                    pool_object.public_name,
                    pool_object.probability_common,
                    pool_object.probability_rare,
                    pool_object.probability_epic,
                    pool_object.probability_legendary,
                    pool_object.price,
                    pool_object.codename,
                ),
            )

            # Update pool items
            if pool_object.items:
                # Delete old items
                delete_items = "DELETE FROM gacha_pools_items WHERE codename = %s"
                cursor.execute(delete_items, (pool_object.codename,))

                # Insert new items
                items_query = "INSERT INTO gacha_pools_items (codename, gacha_uuid) VALUES (%s, UUID_TO_BIN(%s))"
                for item_uuid in pool_object.items:
                    cursor.execute(items_query, (pool_object.codename, item_uuid))

            connection.commit()
            cursor.close()
            return "", 200

        return update_pool_in_db()

    except (
        OperationalError,
        DataError,
        DatabaseError,
        IntegrityError,
        InterfaceError,
        InternalError,
        ProgrammingError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503
