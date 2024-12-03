import requests
import datetime
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
from openapi_server.models.exists_profile200_response import ExistsProfile200Response
from openapi_server.models.get_currency_from_uuid200_response import (
    GetCurrencyFromUuid200Response,
)
from openapi_server.models.get_username_from_uuid200_response import (
    GetUsernameFromUuid200Response,
)
from openapi_server.models.get_uuid_from_username200_response import (
    GetUuidFromUsername200Response,
)
from openapi_server.models.user import User
from openapi_server.models.user_full import UserFull

MOCK_USERS = {
    'e3b0c44298fc1c14b39f92d1282048c0': ("jotaro@joestar.com", "$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy", "USER"),
    '87f3b5d15e8e4fa4909b3cd29f4b1f09': ("dio.brando@world.com", "$2a$12$YUKGEXCU2rGtqnkeStuL6.3SA5IIsBdAC9qv9mrXm4Pa/mLIYPu/K", "USER"),
    'a4f0c59212af4bdeaacd94cd0f27c57e': ("giorno@passione.it", "$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja", "USER"),
    'b5c3d2e14f5e6a7b8c9d0e1f2a3b4c5d': ("josuke@morioh.jp", "$2a$12$4N3oX0NTo5ccUZmCBpCx/uSe14rtSd1E/sZhbOK2eclfQ3o.gdHCa", "USER"),
    '4f2e8bb538e145379cfa11425c3b4284': ("speedwagon@foundation.org", "$2a$12$9HgqzV4s6zhKCBFRMuUGSONqS2bhIQqzpiF1U/K/VW1ofYWyU2mIa", "ADMIN"),
    'a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6': ("admin@admin.com", "$2a$12$Io8F/0QZ8hLSZ.CtqUvM0uK/jhmdXohCFXiby/nHk3ePmzNf1wRhe", "ADMIN"),
}

MOCK_FEEDBACKS = {
    ('e3b0c44298fc1c14b39f92d1282048c0', '2024-01-10 12:00:00'): ('Yare yare daze... Great game!', '2024-01-10 12:00:00'),
    ('87f3b5d15e8e4fa4909b3cd29f4b1f09', '2024-01-11 13:30:00'): ('WRYYYYY! Amazing stands!', '2024-01-11 13:30:00'),
    ('a4f0c59212af4bdeaacd94cd0f27c57e', '2024-01-12 15:45:00'): ('This is... Requiem. Awesome gameplay!', '2024-01-12 15:45:00')
}

MOCK_BUNDLESTRANSACTIONS = {
    ("e3b0c44298fc1c14b39f92d1282048c0", "bundle_arrowEUR", "2024-01-05 10:00:00"): ("bundle_arrowEUR", "EUR", "e3b0c44298fc1c14b39f92d1282048c0", "2024-01-05 10:00:00"),
    ("87f3b5d15e8e4fa4909b3cd29f4b1f09", "bundle_heavenUSD", "2024-01-06 11:30:00"): ("bundle_heavenUSD", "USD", "87f3b5d15e8e4fa4909b3cd29f4b1f09", "2024-01-06 11:30:00"),
    ("a4f0c59212af4bdeaacd94cd0f27c57e", "bundle_requiemEUR", "2024-01-07 15:45:00"): ("bundle_requiemEUR", "EUR", "a4f0c59212af4bdeaacd94cd0f27c57e", "2024-01-07 15:45:00"),
}

MOCK_INGAMETRANSACTIONS = {
    ("e3b0c44298fc1c14b39f92d1282048c0", "2024-01-05 10:00:00"): ("e3b0c44298fc1c14b39f92d1282048c0", 1000, "bought_bundle", "2024-01-05 10:00:00"),
    ("87f3b5d15e8e4fa4909b3cd29f4b1f09", "2024-01-06 11:30:00"): ("87f3b5d15e8e4fa4909b3cd29f4b1f09", 5000, "bought_bundle", "2024-01-06 11:30:00"),
    ("a4f0c59212af4bdeaacd94cd0f27c57e", "2024-01-07 15:45:00"): ("a4f0c59212af4bdeaacd94cd0f27c57e", 3000, "bought_bundle", "2024-01-07 15:45:00"),
    ("e3b0c44298fc1c14b39f92d1282048c0", "2024-01-08 09:15:00"): ("e3b0c44298fc1c14b39f92d1282048c0", -1000, "gacha_pull", "2024-01-08 09:15:00"),
    ('87f3b5d15e8e4fa4909b3cd29f4b1f09', '2024-01-09 14:20:00'): ('87f3b5d15e8e4fa4909b3cd29f4b1f09', -1200, "gacha_pull", '2024-01-09 14:20:00')
}

MOCK_INVENTORIES = {'f7e6d5c4b3a291807654321098fedcba': ('e3b0c44298fc1c14b39f92d1282048c0', '1b2f7b4e5e1f4112a7c5b7559dbb8c76', '2024-01-01', 1, 3000), 'e6d5c4b3a29180765432109876fedcba': ('87f3b5d15e8e4fa4909b3cd29f4b1f09', '9d4b9fa96c7244f59ac6e6b548cfc632', '2024-01-02', 1, 3000), 'd5c4b3a29180765432109876fedcba98': ('a4f0c59212af4bdeaacd94cd0f27c57e', 'b6e7f8c97f284b4f8fbe523f6c8b0c85', '2024-01-03', 1, 2500), 'c7b6a5d4e3f210987654fedcba987654': ('4f2e8bb538e145379cfa11425c3b4284', '1b2f7b4e5e1f4112a7c5b7559dbb8c76', '2024-01-01', 1, 5000), 'b7a6c5d4e3f210987654fedcba987655': ('4f2e8bb538e145379cfa11425c3b4284', '9d4b9fa96c7244f59ac6e6b548cfc632', '2024-01-02', 1, 5000), 'a7b6c5d4e3f210987654fedcba987656': ('4f2e8bb538e145379cfa11425c3b4284', 'b6e7f8c97f284b4f8fbe523f6c8b0c85', '2024-01-03', 1, 3000), '97b6c5d4e3f210987654fedcba987657': ('4f2e8bb538e145379cfa11425c3b4284', '8f2b9d4e3b3e4c5da1c6b7e3a5d6c1c7', '2024-01-04', 1, 3000), '87b6c5d4e3f210987654fedcba987658': ('4f2e8bb538e145379cfa11425c3b4284', 'c1d2e3f45a6b7c8d9e0f1a2b3c4d5e6f', '2024-01-05', 1, 2000), '77b6c5d4e3f210987654fedcba987659': ('4f2e8bb538e145379cfa11425c3b4284', 'd4e5f6a7b8c90d1e2f3a4b5c6d7e8f9a', '2024-01-06', 1, 1000), '67b6c5d4e3f210987654fedcba987660': ('4f2e8bb538e145379cfa11425c3b4284', 'e7f8a9b0c1d23e4f5a6b7c8d9e0f1a2b', '2024-01-07', 1, 2000), '57b6c5d4e3f210987654fedcba987661': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'c3d4e5f6a7b8901234567890abcdef12', '2024-01-08', 1, 5000), '47b6c5d4e3f210987654fedcba987662': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'a1b2c3d4e5f678901234567890abcdef', '2024-01-09', 1, 5000), '37b6c5d4e3f210987654fedcba987663': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'b2c3d4e5f6a78901234567890abcdef1', '2024-01-10', 1, 3000), '27b6c5d4e3f210987654fedcba987664': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'e5f6a7b8c9d01234567890abcdef1234', '2024-01-11', 1, 3000), '17b6c5d4e3f210987654fedcba987665': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'f6a7b8c9d0e1234567890abcdef12345', '2024-01-12', 1, 2000), '07b6c5d4e3f210987654fedcba987666': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'c9d0e1f2a3b456789012cdef12345678', '2024-01-13', 1, 1000), 'f6b6c5d4e3f210987654fedcba987667': ('a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6', 'a7b8c9d0e1f234567890abcdef123456', '2024-01-14', 1, 2000)}

MOCK_AUCTIONS = {
    "aabbccddeeff00112233445566778899": (
        "f7e6d5c4b3a291807654321098fedcba",
        5000,
        6000,
        "87f3b5d15e8e4fa4909b3cd29f4b1f09",
        "2024-02-01 00:00:00"
    ),
    "a9b8c7d6e5f432109876fedcba987654": (
        "c7b6a5d4e3f210987654fedcba987654",
        5000,
        6500,
        "e3b0c44298fc1c14b39f92d1282048c0",
        "2024-02-01 00:00:00"
    ),
}

MOCK_PROFILES = {
    "e3b0c44298fc1c14b39f92d1282048c0": (
        "JotaroKujo",
        5000,
        100,
        "2024-01-05 10:00:00"
    ),
    "87f3b5d15e8e4fa4909b3cd29f4b1f09": (
        "DIOBrando",
        6000,
        95,
        "2024-01-05 11:00:00"
    ),
    "a4f0c59212af4bdeaacd94cd0f27c57e": (
        "GiornoGiovanna",
        4500,
        85,
        "2024-01-05 12:00:00"
    ),
    "b5c3d2e14f5e6a7b8c9d0e1f2a3b4c5d": (
        "JosukeHigashikata",
        3500,
        80,
        "2024-01-05 13:00:00"
    ),
    "4f2e8bb538e145379cfa11425c3b4284": (
        "SpeedwagonAdmin",
        10000,
        98,
        "2024-01-05 14:00:00"
    ),
    "a1a2a3a4b5b6c7c8d9d0e1e2e3e4e5e6": (
        "AdminUser",
        100000000,
        999,
        "2024-01-05 15:00:00"
    ),
}

MOCK_PVPMATCHES = {
    "a1b2c3d4e5f67890abcdef1234567890": (
        "e3b0c44298fc1c14b39f92d1282048c0",  # player1uuid (Jotaro)
        "87f3b5d15e8e4fa4909b3cd29f4b1f09",  # player2uuid (DIO)
        True,  # winner
        {
            "match": {
                "pvp_match_uuid": "a1b2c3d4e5f67890abcdef1234567890",
                "sender_id": "e3b0c44298fc1c14b39f92d1282048c0",
                "receiver_id": "87f3b5d15e8e4fa4909b3cd29f4b1f09",
                "teams": {
                    "team1": ["1b2f7b4e5e1f4112a7c5b7559dbb8c76"],
                    "team2": ["9d4b9fa96c7244f59ac6e6b548cfc632"]
                },
                "winner": True,
                "match_log": {
                    "pairings": [
                        {
                            "pair": "Jotaro StarPlatinum vs DIO TheWorld",
                            "extracted_stat": "power",
                            "player1": {"stand_stat": 5},
                            "player2": {"stand_stat": 5}
                        }
                    ]
                }
            },
            "points": 25
        },  # match_log
        "2024-01-15 12:00:00",  # timestamp
        None  # gachas_types_used (non fornito nei dati)
    ),
    "b2c3d4e5f6a78901bcdef12345678901": (
        "a4f0c59212af4bdeaacd94cd0f27c57e",  # player1uuid (Giorno)
        "87f3b5d15e8e4fa4909b3cd29f4b1f09",  # player2uuid (DIO)
        True,  # winner
        {
            "match": {
                "pvp_match_uuid": "b2c3d4e5f6a78901bcdef12345678901",
                "sender_id": "a4f0c59212af4bdeaacd94cd0f27c57e",
                "receiver_id": "87f3b5d15e8e4fa4909b3cd29f4b1f09",
                "teams": {
                    "team1": ["b6e7f8c97f284b4f8fbe523f6c8b0c85"],
                    "team2": ["9d4b9fa96c7244f59ac6e6b548cfc632"]
                },
                "winner": True,
                "match_log": {
                    "pairings": [
                        {
                            "pair": "Giorno GoldExperience vs DIO TheWorld",
                            "extracted_stat": "potential",
                            "player1": {"stand_stat": 5},
                            "player2": {"stand_stat": 5}
                        }
                    ]
                }
            },
            "points": 30
        },  # match_log
        "2024-01-16 15:30:00",  # timestamp
        None  # gachas_types_used (non fornito nei dati)
    ),
}


SERVICE_TYPE="profile"
circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.HTTPError, OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])

def add_currency(session=None, uuid=None, amount=None):
    """Adds amount to user currency field by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param amount: Amount to add
    :type amount: int
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not amount:
        return "", 400

    try:
        @circuit_breaker
        def update_user_currency():
            # First check if user exists
            if uuid not in MOCK_PROFILES:
                return "", 404
            
            # If user exists, update currency
            MOCK_PROFILES[uuid][1] = MOCK_PROFILES[uuid][1] + amount
            return "", 200

        return update_user_currency()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def add_pvp_score(session=None, uuid=None, points_to_add=None):
    """Adds amount to user pvp_score field by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param amount: Amount to add
    :type amount: int
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not points_to_add:
        return "", 400

    try:
        @circuit_breaker
        def update_user_pvp_score():
            # First check if user exists
            if uuid not in MOCK_PROFILES:
                return "", 404

            # If user exists, update currency
            MOCK_PROFILES[uuid][2] = MOCK_PROFILES[uuid][2] + points_to_add
            return "", 200

        return update_user_pvp_score()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def delete_profile_by_uuid(session=None, uuid=None):
    """Deletes user profile by uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def delete_user_profile():
            global MOCK_PROFILES
            # Check if user exists
            if uuid not in MOCK_PROFILES:
                return "", 404

            # Delete profile
            MOCK_PROFILES = {
                k: v for k, v in MOCK_PROFILES.items() if k != uuid
            }
            return "", 200

        return delete_user_profile()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def edit_username(session=None, uuid=None, username=None):
    """Edits the username.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param username: New username
    :type username: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str) or not username:
        return "", 400
    

    try:
        @circuit_breaker
        def update_username():
            # Check if user exists and get current username
            if uuid not in MOCK_PROFILES:
                return "", 404
                
            # Check if username is the same
            if MOCK_PROFILES[uuid][0] == username:
                return "", 304
            
            # Update username
            MOCK_PROFILES[uuid][0] = username
            return "", 200

        return update_username()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def exists_profile(session=None, uuid=None):
    """Returns true if a profile exists, false otherwise.
    
    :param session: Session cookie
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :rtype: Union[ExistsProfile200Response, Tuple[ExistsProfile200Response, int], Tuple[ExistsProfile200Response, int, Dict[str, str]]]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def check_profile_exists():
            if uuid not in MOCK_PROFILES:
                result = None
            else:
                result = MOCK_PROFILES[uuid]
            return result is not None

        exists = check_profile_exists()
        return jsonify({"exists": exists}), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_currency_from_uuid(session=None, user_uuid=None):
    """Returns currency of the requested user.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[GetCurrencyFromUuid200Response, Tuple[GetCurrencyFromUuid200Response, int], Tuple[GetCurrencyFromUuid200Response, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_currency():
            # Check if user exists and get currency
            if user_uuid not in MOCK_PROFILES:
                result = [MOCK_PROFILES[user_uuid][1]]
            else:
                result = None
            
            if not result:
                return "", 404
                
            return jsonify({"currency": result[0]}), 200

        return get_user_currency()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_profile(session=None, user_uuid=None):
    """Returns profile info.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[User, Tuple[User, int], Tuple[User, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_profile():
            if user_uuid not in MOCK_PROFILES:
                return "", 404
            
            result = MOCK_PROFILES[user_uuid]
            profile = {
                "username": result[0],
                "currency": result[1],
                "pvp_score": result[2],
                "created_at": result[3]
            }
            
            return jsonify(profile), 200

        return get_user_profile()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_username_from_uuid(session=None, user_uuid=None):
    """Returns username of the requested user.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :rtype: Union[GetUsernameFromUuid200Response, Tuple[GetUsernameFromUuid200Response, int], Tuple[GetUsernameFromUuid200Response, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_username():
            if user_uuid not in MOCK_PROFILES:
                return "", 404
            
            result = MOCK_PROFILES[user_uuid][0]
                
            return jsonify({"username": result[0]}), 200

        return get_user_username()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503


def get_uuid_from_username(session=None, username=None):
    if not username:
        return jsonify({"error": "Invalid request."}), 400
    
    try:
        @circuit_breaker
        def make_request_to_db():
            result = None
            for k, v in MOCK_PROFILES.items():
                if v[0] == username:
                    result["uuid"] = k
            return result
        
        result = make_request_to_db()

        if not result:
            return "", 404
        return result["uuid"]

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def insert_profile(session=None, user_uuid=None, username=None):
    """Creates a profile.
    
    :param session: Session cookie
    :type session: str
    :param user_uuid: User UUID
    :type user_uuid: str
    :param username: Username
    :type username: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if not user_uuid or not isinstance(user_uuid, str) or not username:
        return "", 400

    try:
        @circuit_breaker
        def create_profile():
            if user_uuid in MOCK_PROFILES:
                return "", 409
            
            for k, v in MOCK_PROFILES.items():
                if v[0] == username:
                    return "", 409
            
            MOCK_PROFILES[user_uuid] = (username, 0, 0, datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
            return "", 201

        return create_profile()

    except (OperationalError, DataError,
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except DatabaseError:
        return "", 409
    except IntegrityError:
        return "",409
    except CircuitBreakerError:
        return "", 503


def profile_list(session=None, page_number=None):
    """Returns list of profiles based on pagenumber.
    
    :param session: Session cookie
    :type session: str
    :param page_number: Page number of the list
    :type page_number: int
    :rtype: Union[List[UserFull], Tuple[List[UserFull], int], Tuple[List[UserFull], int, Dict[str, str]]]
    """
    # Validate page_number
    if page_number and not isinstance(page_number, (int, str)):
        return "", 400
        
    try:
        page_number = int(page_number) if page_number is not None else 1
        if page_number < 1:
            return "", 400
    except (TypeError, ValueError):
        return "", 400

    try:
        @circuit_breaker
        def get_profiles():
            items_per_page = 10
            offset = (page_number - 1) * items_per_page

            # Convert the MOCK_PROFILES dictionary to a list
            profiles_list = [
                {
                    "uuid": uuid,
                    "username": data[0],
                    "currency": data[1],
                    "pvp_score": data[2],
                    "created_at": data[3]
                }
                for uuid, data in MOCK_PROFILES.items()
            ]

            # Paginate the profiles list
            paginated_profiles = profiles_list[offset:offset + items_per_page]

            return jsonify(paginated_profiles), 200

        return get_profiles()

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError):
        return "", 503
    except CircuitBreakerError:
        return "", 503