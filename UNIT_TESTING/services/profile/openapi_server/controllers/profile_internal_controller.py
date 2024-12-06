############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import datetime
import requests
from flask import jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

MOCK_USERS = {
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": (
        "jotaro@joestar.com",
        "$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy",
        "USER",
    ),
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": (
        "dio.brando@world.com",
        "$2a$12$YUKGEXCU2rGtqnkeStuL6.3SA5IIsBdAC9qv9mrXm4Pa/mLIYPu/K",
        "USER",
    ),
    "a4f0c592-12af-4bde-aacd-94cd0f27c57e": (
        "giorno@passione.it",
        "$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja",
        "USER",
    ),
    "b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d": (
        "josuke@morioh.jp",
        "$2a$12$4N3oX0NTo5ccUZmCBpCx/uSe14rtSd1E/sZhbOK2eclfQ3o.gdHCa",
        "USER",
    ),
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284": (
        "speedwagon@foundation.org",
        "$2a$12$9HgqzV4s6zhKCBFRMuUGSONqS2bhIQqzpiF1U/K/VW1ofYWyU2mIa",
        "ADMIN",
    ),
    "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6": (
        "admin@admin.com",
        "$2a$12$Io8F/0QZ8hLSZ.CtqUvM0uK/jhmdXohCFXiby/nHk3ePmzNf1wRhe",
        "ADMIN",
    ),
}

MOCK_FEEDBACKS = {
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "2024-01-10 12:00:00"): (
        "Yare yare daze... Great game!",
        "2024-01-10 12:00:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "2024-01-11 13:30:00"): (
        "WRYYYYY! Amazing stands!",
        "2024-01-11 13:30:00",
    ),
    ("a4f0c592-12af-4bde-aacd-94cd0f27c57e", "2024-01-12 15:45:00"): (
        "This is... Requiem. Awesome gameplay!",
        "2024-01-12 15:45:00",
    ),
}

MOCK_BUNDLESTRANSACTIONS = {
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "bundle_arrowEUR", "2024-01-05 10:00:00"): (
        "bundle_arrowEUR",
        "EUR",
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "2024-01-05 10:00:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "bundle_heavenUSD", "2024-01-06 11:30:00"): (
        "bundle_heavenUSD",
        "USD",
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "2024-01-06 11:30:00",
    ),
    ("a4f0c592-12af-4bde-aacd-94cd0f27c57e", "bundle_requiemEUR", "2024-01-07 15:45:00"): (
        "bundle_requiemEUR",
        "EUR",
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "2024-01-07 15:45:00",
    ),
}

MOCK_INGAMETRANSACTIONS = {
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "2024-01-05 10:00:00"): (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        1000,
        "bought_bundle",
        "2024-01-05 10:00:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "2024-01-06 11:30:00"): (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        5000,
        "bought_bundle",
        "2024-01-06 11:30:00",
    ),
    ("a4f0c592-12af-4bde-aacd-94cd0f27c57e", "2024-01-07 15:45:00"): (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        3000,
        "bought_bundle",
        "2024-01-07 15:45:00",
    ),
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "2024-01-08 09:15:00"): (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        -1000,
        "gacha_pull",
        "2024-01-08 09:15:00",
    ),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "2024-01-09 14:20:00"): (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        -1200,
        "gacha_pull",
        "2024-01-09 14:20:00",
    ),
}

MOCK_INVENTORIES = {
    "f7e6d5c4-b3a2-9180-7654-321098fedcba": (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "2024-01-01",
        1,
        3000,
    ),
    "e6d5c4b3-a291-8076-5432-109876fedcba": (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        3000,
    ),
    "d5c4b3a2-9180-7654-3210-9876fedcba98": (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        2500,
    ),
    "c7b6a5d4-e3f2-1098-7654-fedcba987654": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76",
        "2024-01-01",
        1,
        5000,
    ),
    "b7a6c5d4-e3f2-1098-7654-fedcba987655": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632",
        "2024-01-02",
        1,
        5000,
    ),
    "a7b6c5d4-e3f2-1098-7654-fedcba987656": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85",
        "2024-01-03",
        1,
        3000,
    ),
    "97b6c5d4-e3f2-1098-7654-fedcba987657": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7",
        "2024-01-04",
        1,
        3000,
    ),
    "87b6c5d4-e3f2-1098-7654-fedcba987658": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
        "2024-01-05",
        1,
        2000,
    ),
    "77b6c5d4-e3f2-1098-7654-fedcba987659": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a",
        "2024-01-06",
        1,
        1000,
    ),
    "67b6c5d4-e3f2-1098-7654-fedcba987660": (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b",
        "2024-01-07",
        1,
        2000,
    ),
    "57b6c5d4-e3f2-1098-7654-fedcba987661": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
        "2024-01-08",
        1,
        5000,
    ),
    "47b6c5d4-e3f2-1098-7654-fedcba987662": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "a1b2c3d4-e5f6-7890-1234-567890abcdef",
        "2024-01-09",
        1,
        5000,
    ),
    "37b6c5d4-e3f2-1098-7654-fedcba987663": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
        "2024-01-10",
        1,
        3000,
    ),
    "27b6c5d4-e3f2-1098-7654-fedcba987664": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "e5f6a7b8-c9d0-1234-5678-90abcdef1234",
        "2024-01-11",
        1,
        3000,
    ),
    "17b6c5d4-e3f2-1098-7654-fedcba987665": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "f6a7b8c9-d0e1-2345-6789-0abcdef12345",
        "2024-01-12",
        1,
        2000,
    ),
    "07b6c5d4-e3f2-1098-7654-fedcba987666": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "c9d0e1f2-a3b4-5678-9012-cdef12345678",
        "2024-01-13",
        1,
        1000,
    ),
    "f6b6c5d4-e3f2-1098-7654-fedcba987667": (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "a7b8c9d0-e1f2-3456-7890-abcdef123456",
        "2024-01-14",
        1,
        2000,
    ),
}

MOCK_AUCTIONS = {
    "aabbccdd-eeff-0011-2233-445566778899": (
        "f7e6d5c4-b3a2-9180-7654-321098fedcba",
        5000,
        6000,
        "87f3b5d1-5e8e-4fa4-909b-3cd29c4b1f09",
        "2025-02-01 00:00:00",
    ),
    "a9b8c7d6-e5f4-3210-9876-fedcba987654": (
        "c7b6a5d4-e3f2-1098-7654-fedcba987654",
        5000,
        6500,
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "2025-02-01 00:00:00",
    ),
}

MOCK_PROFILES = {
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": (
        "JotaroKujo",
        5000,
        100,
        "2024-01-05 10:00:00",
    ),
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": (
        "DIOBrando",
        16000,
        95,
        "2024-01-05 11:00:00",
    ),
    "a4f0c592-12af-4bde-aacd-94cd0f27c57e": (
        "GiornoGiovanna",
        4500,
        85,
        "2024-01-05 12:00:00",
    ),
    "b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d": (
        "JosukeHigashikata",
        3500,
        80,
        "2024-01-05 13:00:00",
    ),
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284": (
        "SpeedwagonAdmin",
        10000,
        98,
        "2024-01-05 14:00:00",
    ),
    "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6": (
        "AdminUser",
        100000000,
        999,
        "2024-01-05 15:00:00",
    ),
}

MOCK_PVPMATCHES = {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        True,
        {
            "match": {
                "match_log": {
                    "pairings": [
                        {
                            "extracted_stat": "power",
                            "pair": "Jotaro " "StarPlatinum " "vs " "DIO " "TheWorld",
                            "player1": {"stand_stat": 5},
                            "player2": {"stand_stat": 5},
                        }
                    ]
                },
                "pvp_match_uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
                "sender_id": "e3b0c442-98fc-1c14-b39f-92d1282048c0",
                "teams": {
                    "team1": ["1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76"],
                    "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"],
                },
                "winner": True,
            },
            "points": 25,
        },
        "2024-01-15 12:00:00",
        None,
    ),
    "b2c3d4e5-f6a7-8901-bcde-f12345678901": (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        True,
        {
            "match": {
                "match_log": {
                    "pairings": [
                        {
                            "extracted_stat": "potential",
                            "pair": "Giorno " "GoldExperience " "vs " "DIO " "TheWorld",
                            "player1": {"stand_stat": 5},
                            "player2": {"stand_stat": 5},
                        }
                    ]
                },
                "pvp_match_uuid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "receiver_id": "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
                "sender_id": "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
                "teams": {
                    "team1": ["b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85"],
                    "team2": ["9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632"],
                },
                "winner": True,
            },
            "points": 30,
        },
        "2024-01-16 15:30:00",
        None,
    ),
}


SERVICE_TYPE = "profile"
circuit_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=5,
    exclude=[
        requests.HTTPError,
    ],
)


def add_currency(session=None, uuid=None, amount=None):
    if not uuid or not isinstance(uuid, str) or not amount:
        return "", 400

    try:

        @circuit_breaker
        def update_user_currency():
            global MOCK_PROFILES

            if uuid not in MOCK_PROFILES:
                return "", 404

            MOCK_PROFILES[uuid] = (
                MOCK_PROFILES[uuid][0],
                MOCK_PROFILES[uuid][1] + amount,
                MOCK_PROFILES[uuid][2],
                MOCK_PROFILES[uuid][3],
            )
            return "", 200

        return update_user_currency()

    except CircuitBreakerError:
        return "", 503


def add_pvp_score(session=None, uuid=None, points_to_add=None):
    if not uuid or not isinstance(uuid, str) or not points_to_add:
        return "", 400

    try:

        @circuit_breaker
        def update_user_pvp_score():
            global MOCK_PROFILES

            if uuid not in MOCK_PROFILES:
                return "", 404

            MOCK_PROFILES[uuid] = (
                MOCK_PROFILES[uuid][0],
                MOCK_PROFILES[uuid][1],
                MOCK_PROFILES[uuid][2] + points_to_add,
                MOCK_PROFILES[uuid][3],
            )
            return "", 200

        return update_user_pvp_score()

    except CircuitBreakerError:
        return "", 503


def delete_profile_by_uuid(session=None, uuid=None):
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:

        @circuit_breaker
        def delete_user_profile():
            global MOCK_PROFILES

            if uuid not in MOCK_PROFILES:
                return "", 404

            MOCK_PROFILES = {k: v for k, v in MOCK_PROFILES.items() if k != uuid}
            return "", 200

        return delete_user_profile()

    except CircuitBreakerError:
        return "", 503


def edit_username(session=None, uuid=None, username=None):
    if not uuid or not isinstance(uuid, str) or not username:
        return "", 400

    try:

        @circuit_breaker
        def update_username():
            global MOCK_PROFILES

            if uuid not in MOCK_PROFILES:
                return "", 404

            if MOCK_PROFILES[uuid][0] == username:
                return "", 304

            MOCK_PROFILES[uuid] = (
                username,
                MOCK_PROFILES[uuid][1],
                MOCK_PROFILES[uuid][2],
                MOCK_PROFILES[uuid][3],
            )
            return "", 200

        return update_username()

    except CircuitBreakerError:
        return "", 503


def exists_profile(session=None, uuid=None):
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:

        @circuit_breaker
        def check_profile_exists():
            global MOCK_PROFILES
            if uuid not in MOCK_PROFILES:
                result = None
            else:
                result = MOCK_PROFILES[uuid]
            return result is not None

        exists = check_profile_exists()
        return jsonify({"exists": exists}), 200

    except CircuitBreakerError:
        return "", 503


def get_currency_from_uuid(session=None, user_uuid=None):
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:

        @circuit_breaker
        def get_user_currency():
            global MOCK_PROFILES

            if user_uuid not in MOCK_PROFILES:
                result = None
            else:
                result = [MOCK_PROFILES[user_uuid][1]]

            if not result:
                return "", 404

            return jsonify({"currency": result[0]}), 200

        return get_user_currency()

    except CircuitBreakerError:
        return "", 503


def get_profile(session=None, user_uuid=None):
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:

        @circuit_breaker
        def get_user_profile():
            global MOCK_PROFILES
            if user_uuid not in MOCK_PROFILES:
                return "", 404

            result = MOCK_PROFILES[user_uuid]
            profile = {
                "username": result[0],
                "currency": result[1],
                "pvp_score": result[2],
                "created_at": result[3],
            }

            return jsonify(profile), 200

        return get_user_profile()

    except CircuitBreakerError:
        return "", 503


def get_username_from_uuid(session=None, user_uuid=None):
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:

        @circuit_breaker
        def get_user_username():
            global MOCK_PROFILES
            if user_uuid not in MOCK_PROFILES:
                return "", 404

            result = MOCK_PROFILES[user_uuid]

            return jsonify({"username": result[0]}), 200

        return get_user_username()

    except CircuitBreakerError:
        return "", 503


def get_uuid_from_username(session=None, username=None):
    if not username:
        return jsonify({"error": "Invalid request."}), 400

    try:

        @circuit_breaker
        def make_request_to_db():
            global MOCK_PROFILES
            result = None
            for k, v in MOCK_PROFILES.items():
                if v[0] == username:
                    result["uuid"] = k
            return result

        result = make_request_to_db()

        if not result:
            return "", 404
        return result["uuid"]
    except CircuitBreakerError:
        return "", 503


def insert_profile(session=None, user_uuid=None, username=None):
    if not user_uuid or not isinstance(user_uuid, str) or not username:
        return "", 400

    try:

        @circuit_breaker
        def create_profile():
            global MOCK_PROFILES
            if user_uuid in MOCK_PROFILES:
                return "", 409

            for k, v in MOCK_PROFILES.items():
                if v[0] == username:
                    return "", 409

            MOCK_PROFILES[user_uuid] = (
                username,
                0,
                0,
                datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
            )
            return "", 201

        return create_profile()

    except CircuitBreakerError:
        return "", 503


def profile_list(session=None, page_number=None):
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
            global MOCK_PROFILES
            items_per_page = 10
            offset = (page_number - 1) * items_per_page

            profiles_list = [
                {
                    "uuid": uuid,
                    "username": data[0],
                    "currency": data[1],
                    "pvp_score": data[2],
                    "created_at": data[3],
                }
                for uuid, data in MOCK_PROFILES.items()
            ]

            paginated_profiles = profiles_list[offset : offset + items_per_page]

            return jsonify(paginated_profiles), 200

        return get_profiles()

    except CircuitBreakerError:
        return "", 503
