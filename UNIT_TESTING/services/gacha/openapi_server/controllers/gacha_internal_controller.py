############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import datetime

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

from openapi_server.models.gacha import Gacha
from openapi_server.models.pool import Pool

MOCK_GACHAS = {
    "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76": (
        "Star Platinum",
        "LEGENDARY",
        100,
        100,
        100,
        100,
        60,
        100,
        datetime.date(2024, 1, 1),
    ),
    "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632": (
        "The World",
        "LEGENDARY",
        100,
        100,
        100,
        100,
        60,
        100,
        datetime.date(2024, 1, 2),
    ),
    "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85": (
        "Gold Experience",
        "EPIC",
        80,
        80,
        80,
        80,
        60,
        100,
        datetime.date(2024, 1, 3),
    ),
    "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7": (
        "Crazy Diamond",
        "EPIC",
        100,
        100,
        80,
        100,
        40,
        80,
        datetime.date(2024, 1, 4),
    ),
    "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f": (
        "Silver Chariot",
        "RARE",
        80,
        100,
        60,
        100,
        60,
        60,
        datetime.date(2024, 1, 5),
    ),
    "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a": (
        "Hermit Purple",
        "COMMON",
        40,
        60,
        60,
        80,
        80,
        40,
        datetime.date(2024, 1, 6),
    ),
    "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b": (
        "Magicians Red",
        "RARE",
        80,
        60,
        60,
        60,
        80,
        60,
        datetime.date(2024, 1, 7),
    ),
    "f1a2b3c4-d5e6-f7a8-b9c0-1d2e3f4a5b6c": (
        "Hierophant Green",
        "RARE",
        60,
        60,
        60,
        100,
        100,
        60,
        datetime.date(2024, 1, 8),
    ),
    "a1b2c3d4-e5f6-7890-1234-567890abcdef": (
        "King Crimson",
        "LEGENDARY",
        100,
        80,
        80,
        80,
        40,
        100,
        datetime.date(2024, 1, 9),
    ),
    "b2c3d4e5-f6a7-8901-2345-67890abcdef1": (
        "Killer Queen",
        "EPIC",
        80,
        80,
        80,
        100,
        60,
        80,
        datetime.date(2024, 1, 10),
    ),
    "c3d4e5f6-a7b8-9012-3456-7890abcdef12": (
        "Made in Heaven",
        "LEGENDARY",
        100,
        100,
        100,
        100,
        100,
        100,
        datetime.date(2024, 1, 11),
    ),
    "d4e5f6a7-b8c9-0123-4567-890abcdef123": (
        "Sticky Fingers",
        "RARE",
        80,
        80,
        60,
        80,
        40,
        60,
        datetime.date(2024, 1, 12),
    ),
    "e5f6a7b8-c9d0-1234-5678-90abcdef1234": (
        "Purple Haze",
        "EPIC",
        100,
        60,
        60,
        40,
        40,
        40,
        datetime.date(2024, 1, 13),
    ),
    "f6a7b8c9-d0e1-2345-6789-0abcdef12345": (
        "Sex Pistols",
        "RARE",
        40,
        60,
        80,
        100,
        100,
        40,
        datetime.date(2024, 1, 14),
    ),
    "a7b8c9d0-e1f2-3456-7890-abcdef123456": ("Aerosmith", "RARE", 60, 80, 60, 80, 100, 40, datetime.date(2024, 1, 15)),
    "b8c9d0e1-f2a3-4567-8901-bcdef1234567": (
        "Moody Blues",
        "RARE",
        40,
        60,
        60,
        100,
        40,
        60,
        datetime.date(2024, 1, 16),
    ),
    "c9d0e1f2-a3b4-5678-9012-cdef12345678": (
        "Beach Boy",
        "COMMON",
        20,
        40,
        60,
        100,
        100,
        40,
        datetime.date(2024, 1, 17),
    ),
    "d0e1f2a3-b4c5-6789-0123-def123456789": (
        "White Album",
        "RARE",
        60,
        60,
        100,
        60,
        40,
        60,
        datetime.date(2024, 1, 18),
    ),
    "e1f2a3b4-c5d6-7890-1234-ef123456789a": ("Stone Free", "EPIC", 80, 80, 80, 100, 60, 80, datetime.date(2024, 1, 19)),
    "f2a3b4c5-d6e7-8901-2345-f123456789ab": (
        "Weather Report",
        "EPIC",
        80,
        60,
        80,
        80,
        80,
        100,
        datetime.date(2024, 1, 20),
    ),
    "a3b4c5d6-e7f8-9012-3456-123456789abc": ("D4C", "LEGENDARY", 100, 80, 100, 80, 60, 100, datetime.date(2024, 1, 21)),
    "b4c5d6e7-f8a9-0123-4567-23456789abcd": (
        "Tusk Act 4",
        "LEGENDARY",
        100,
        60,
        100,
        80,
        60,
        100,
        datetime.date(2024, 1, 22),
    ),
    "c5d6e7f8-a9b0-1234-5678-3456789abcde": (
        "Soft & Wet",
        "EPIC",
        80,
        80,
        80,
        100,
        40,
        100,
        datetime.date(2024, 1, 23),
    ),
}


MOCK_POOLS = {
    "pool_joestar": ("Joestar Legacy Pool", 0.50, 0.30, 0.15, 0.05, 1000),
    "pool_passione": ("Passione Gang Pool", 0.45, 0.35, 0.15, 0.05, 1200),
    "pool_duwang": ("Morioh Pool", 0.40, 0.35, 0.20, 0.05, 1500),
    "pool_pucci": ("Heaven Pool", 0.30, 0.30, 0.30, 0.10, 2000),
    "pool_valentine": ("Patriot Pool", 0.40, 0.30, 0.20, 0.10, 1800),
}
MOCK_POOL_ITEMS = {
    "pool_joestar": [
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
        "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7",
        "e1f2a3b4-c5d6-7890-1234-ef123456789a",
        "b4c5d6e7-f8a9-0123-4567-23456789abcd",
        "c5d6e7f8-a9b0-1234-5678-3456789abcde",
    ],
    "pool_passione": [
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "d4e5f6a7-b8c9-0123-4567-890abcdef123",
        "e5f6a7b8-c9d0-1234-5678-90abcdef1234",
        "f6a7b8c9-d0e1-2345-6789-0abcdef12345",
        "a7b8c9d0-e1f2-3456-7890-abcdef123456",
        "b8c9d0e1-f2a3-4567-8901-bcdef1234567",
    ],
    "pool_duwang": [
        "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7",
        "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
        "c9d0e1f2-a3b4-5678-9012-cdef12345678",
        "d0e1f2a3-b4c5-6789-0123-def123456789",
    ],
    "pool_pucci": [
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
        "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "f2a3b4c5-d6e7-8901-2345-f123456789ab",
    ],
    "pool_valentine": [
        "a3b4c5d6-e7f8-9012-3456-123456789abc",
        "b4c5d6e7-f8a9-0123-4567-23456789abcd",
        "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
        "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b",
    ],
}

circuit_breaker = CircuitBreaker(
    fail_max=1000,
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


def create_gacha(gacha=None, session=None):
    """Creates gacha requested."""
    if not connexion.request.is_json:
        return "", 400

    try:

        @circuit_breaker
        def insert_gacha():
            global MOCK_GACHAS
            gacha_data = Gacha.from_dict(connexion.request.get_json())
            uuid = gacha_data.gacha_uuid

            if uuid in MOCK_GACHAS:  # Check for duplicate UUID
                raise IntegrityError("Duplicate entry")  # Simulate a database IntegrityError

            stats = {
                stat: 120 - (ord(getattr(gacha_data.attributes, stat).upper()) - ord("A")) * 20
                for stat in ["power", "speed", "durability", "precision", "range", "potential"]
            }

            MOCK_GACHAS[uuid] = (gacha_data.name, gacha_data.rarity.upper(), *stats.values(), datetime.date.today())

            return "", 201

        return insert_gacha()

    except IntegrityError:  # Simulate database error (duplicate UUID)
        return "", 409  # Conflict if UUID exists
    except (
        OperationalError,
        DataError,
        ProgrammingError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):  # other potential errors
        return "", 503
    except CircuitBreakerError:
        return "", 503


def create_pool(pool=None, session=None):
    """Creates pool requested."""
    if not connexion.request.is_json:
        return "", 400

    try:
        pool_data = Pool.from_dict(connexion.request.get_json())
        codename = pool_data.codename

        @circuit_breaker
        def insert_pool():
            global MOCK_POOLS, MOCK_POOL_ITEMS
            if codename in MOCK_POOLS:
                return "Pool with this codename already exists", 409

            if not all(uuid in MOCK_GACHAS for uuid in pool_data.items):
                return "Some items don't exist", 400

            MOCK_POOLS[codename] = (
                pool_data.public_name,
                pool_data.probability_common,
                pool_data.probability_rare,
                pool_data.probability_epic,
                pool_data.probability_legendary,
                pool_data.price,
            )
            MOCK_POOL_ITEMS[codename] = pool_data.items  # Add items to MOCK_POOL_ITEMS

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
    """Deletes requested gacha."""
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def delete_gacha_from_db():
            global MOCK_GACHAS, MOCK_POOL_ITEMS

            if uuid not in MOCK_GACHAS:
                return "", 404

            del MOCK_GACHAS[uuid]

            # Remove gacha from all pools in MOCK_POOL_ITEMS
            for pool_codename, gacha_list in MOCK_POOL_ITEMS.items():  # Iterate through pool items
                MOCK_POOL_ITEMS[pool_codename] = [g for g in gacha_list if g != uuid]

            return "", 200

        return delete_gacha_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_pool(session=None, codename=None):
    """Deletes requested pool."""
    if not codename:
        return "", 400

    try:

        @circuit_breaker
        def delete_pool_from_db():
            global MOCK_POOLS, MOCK_POOL_ITEMS

            if codename not in MOCK_POOLS:  # Check if the pool exists
                return "", 404

            del MOCK_POOLS[codename]  # Remove pool
            del MOCK_POOL_ITEMS[codename]  # Remove associated pool items

            return "", 200

        return delete_pool_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_gacha(session=None, uuid=None):
    """Returns true if a gacha exists, false otherwise."""
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def check_gacha_exists():
            global MOCK_GACHAS  # Make sure to access the global here
            return jsonify({"exists": uuid in MOCK_GACHAS}), 200

        return check_gacha_exists()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_pool(session=None, uuid=None):  # uuid is actually the codename
    """Returns true if a pool exists, false otherwise."""
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def check_pool_exists():
            global MOCK_POOLS

            pool_exists = uuid in MOCK_POOLS  # Efficient existence check

            return jsonify({"exists": pool_exists}), 200

        return check_pool_exists()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_gacha(session=None, uuid=None):
    """Returns the gacha object by gacha uuid."""
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def get_gacha_from_db():
            global MOCK_GACHAS

            gacha_data = MOCK_GACHAS.get(uuid)  # Use .get() to handle missing UUID

            if not gacha_data:
                return {"error": "Gacha not found"}, 404

            name, rarity, power, speed, durability, precision, range_, potential, release_date = (
                gacha_data  # Unpack tuple
            )

            # Construct the Gacha object for the response
            gacha_obj = {
                "gacha_uuid": uuid,
                "name": name,
                "rarity": rarity,
                "attributes": {
                    "power": chr(ord("F") - (power // 20) + 1),  # Convert stat back to letter grade
                    "speed": chr(ord("F") - (speed // 20) + 1),
                    "durability": chr(ord("F") - (durability // 20) + 1),
                    "precision": chr(ord("F") - (precision // 20) + 1),
                    "range": chr(ord("F") - (range_ // 20) + 1),
                    "potential": chr(ord("F") - (potential // 20) + 1),
                },
            }

            return gacha_obj, 200

        return get_gacha_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_pool(session=None, uuid=None):  # Note: uuid is actually codename
    """Returns the pool object by pool codename."""
    if not uuid:  # Check if codename is provided
        return "", 400

    try:

        @circuit_breaker
        def get_pool_from_db():
            global MOCK_POOLS, MOCK_POOL_ITEMS

            pool_data = MOCK_POOLS.get(uuid)  # Retrieve pool data using codename (uuid)
            if not pool_data:
                return "", 404  # Pool not found

            public_name, prob_common, prob_rare, prob_epic, prob_legendary, price = pool_data
            items = MOCK_POOL_ITEMS.get(uuid, [])  # Retrieve pool items

            pool_obj = {
                "codename": uuid,  # Using uuid (which is the codename)
                "public_name": public_name,
                "probability_common": prob_common,
                "probability_rare": prob_rare,
                "probability_epic": prob_epic,
                "probability_legendary": prob_legendary,
                "price": price,
                "items": items,  # Include the list of items
            }
            return jsonify(pool_obj), 200

        return get_pool_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_rarity_by_uuid(session=None, uuid=None):
    """Returns the rarity of a gacha."""
    if not uuid:
        return "", 400

    try:

        @circuit_breaker
        def get_rarity_from_db():
            global MOCK_GACHAS

            gacha_data = MOCK_GACHAS.get(uuid)
            if not gacha_data:
                return "", 404  # Gacha not found

            rarity = gacha_data[1]  # Extract rarity (second element in the tuple)

            return jsonify({"rarity": rarity}), 200

        return get_rarity_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def list_gachas(requestBody=None, session=None, not_owned=None):
    """Returns a list of gachas by UUIDs."""

    if not connexion.request.is_json:  # Check if the request is JSON
        return "", 400

    requestBody = connexion.request.get_json()  # Get the request body *outside* the nested function!!!

    if not requestBody:  # Check if the request body is empty
        return "", 400

    try:

        @circuit_breaker
        def get_gachas_from_db():
            global MOCK_GACHAS

            requested_uuids = requestBody
            gachas = []

            for uuid in requested_uuids:
                gacha_data = MOCK_GACHAS.get(uuid)
                if gacha_data:
                    name, rarity, power, speed, durability, precision, range_, potential, release_date = gacha_data
                    gacha_obj = {
                        "gacha_uuid": uuid,
                        "name": name,
                        "rarity": rarity,
                        "attributes": {
                            "power": chr(ord("F") - (power // 20) + 1),  # Correct conversion
                            "speed": chr(ord("F") - (speed // 20) + 1),  # Correct conversion
                            "durability": chr(ord("F") - (durability // 20) + 1),  # Correct conversion
                            "precision": chr(ord("F") - (precision // 20) + 1),  # Correct conversion
                            "range": chr(ord("F") - (range_ // 20) + 1),  # Correct conversion
                            "potential": chr(ord("F") - (potential // 20) + 1),  # Correct conversion
                        },
                    }
                    gachas.append(gacha_obj)

            return jsonify(gachas), 200

        return get_gachas_from_db()  # Call the nested function

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def list_pools(session=None):
    """Returns list of pools."""

    try:

        @circuit_breaker
        def get_pools_from_db():
            global MOCK_POOLS, MOCK_POOL_ITEMS
            pools = []

            for codename, pool_data in MOCK_POOLS.items():
                public_name, prob_common, prob_rare, prob_epic, prob_legendary, price = pool_data
                items = MOCK_POOL_ITEMS.get(codename, [])  # Get items or empty list if none

                pool_obj = {
                    "codename": codename,
                    "public_name": public_name,
                    "probability_common": prob_common,
                    "probability_rare": prob_rare,
                    "probability_epic": prob_epic,
                    "probability_legendary": prob_legendary,
                    "price": price,
                    "items": items,  # Include associated items
                }
                pools.append(pool_obj)

            return pools, 200

        return get_pools_from_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def update_gacha(gacha=None, session=None):
    """Updates a gacha."""
    if not connexion.request.is_json:
        return "", 400

    try:
        gacha_data = connexion.request.get_json()
        if not gacha_data:
            return "", 400

        gacha_obj = Gacha.from_dict(gacha_data)  # Get Gacha object from request
        uuid = gacha_obj.gacha_uuid

        # Validate rarity:
        valid_rarities = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
        if gacha_obj.rarity.upper() not in valid_rarities:
            return "", 400

        @circuit_breaker
        def update_gacha_in_db():
            global MOCK_GACHAS

            if uuid not in MOCK_GACHAS:
                return "", 404  # Gacha not found

            # Get the current gacha data for comparison (and unpack)
            (
                current_name,
                current_rarity,
                current_power,
                current_speed,
                current_durability,
                current_precision,
                current_range,
                current_potential,
                current_release_date,
            ) = MOCK_GACHAS[uuid]

            stats = {
                stat: 120 - (ord(getattr(gacha_obj.attributes, stat).upper()) - ord("A")) * 20
                for stat in ["power", "speed", "durability", "precision", "range", "potential"]
            }

            # Check if values have changed (compare stats and rarity, skip name and release date)
            if (
                gacha_obj.rarity.upper() == current_rarity
                and stats["power"] == current_power
                and stats["speed"] == current_speed
                and stats["durability"] == current_durability
                and stats["precision"] == current_precision
                and stats["range"] == current_range
                and stats["potential"] == current_potential
            ):
                return "", 304  # Not Modified

            MOCK_GACHAS[uuid] = (
                gacha_obj.name,
                gacha_obj.rarity.upper(),
                *stats.values(),
                current_release_date,
            )  # Update with corrected stats conversion and preserve release_date

            return "", 200  # OK

        return update_gacha_in_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def update_pool(pool=None, session=None):
    """Updates a pool."""
    if not connexion.request.is_json:
        return "", 400

    try:
        pool_data = connexion.request.get_json()
        if not pool_data:
            return "", 400

        pool_obj = Pool.from_dict(pool_data)
        codename = pool_obj.codename
        price = pool_obj.price

        # Validate probabilities
        total_prob = (
            pool_obj.probability_common
            + pool_obj.probability_rare
            + pool_obj.probability_epic
            + pool_obj.probability_legendary
        )

        if not 0.99 <= total_prob <= 1.01:
            return "", 400

        if price <= 0:  # Use the default or provided price here
            return "", 400

        @circuit_breaker
        def update_pool_in_db():
            global MOCK_POOLS, MOCK_POOL_ITEMS

            if codename not in MOCK_POOLS:
                return "", 404

            if pool_obj.items and not all(item in MOCK_GACHAS for item in pool_obj.items):
                return "", 400

            current_pool = MOCK_POOLS[codename]

            if (
                pool_obj.public_name == current_pool[0]
                and pool_obj.probability_common == current_pool[1]
                and pool_obj.probability_rare == current_pool[2]
                and pool_obj.probability_epic == current_pool[3]
                and pool_obj.probability_legendary == current_pool[4]
                and price == current_pool[5]
            ):
                current_items = MOCK_POOL_ITEMS.get(codename)
                if current_items is not None and set(pool_obj.items) == set(current_items):
                    return "", 304

            MOCK_POOLS[codename] = (
                pool_obj.public_name,
                pool_obj.probability_common,
                pool_obj.probability_rare,
                pool_obj.probability_epic,
                pool_obj.probability_legendary,
                price,
            )  # Use price here as well
            MOCK_POOL_ITEMS[codename] = pool_obj.items

            return "", 200

        return update_pool_in_db()

    except (
        OperationalError,
        DataError,
        ProgrammingError,
        IntegrityError,
        InternalError,
        InterfaceError,
        DatabaseError,
    ):
        return "", 503
    except CircuitBreakerError:
        return "", 503
