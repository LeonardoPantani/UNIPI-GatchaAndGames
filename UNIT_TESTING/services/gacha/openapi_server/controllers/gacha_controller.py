############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import random
import uuid
from datetime import datetime

import connexion
import requests
from flask import jsonify
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.controllers.gacha_internal_controller import exists_pool, get_gacha, get_pool, list_pools
from openapi_server.helpers.authorization import verify_login  # If you're mocking authentication
from openapi_server.helpers.input_checks import sanitize_string_input  # input checks are important and are NOT mocked

circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[requests.exceptions.HTTPError])


GACHA_SERVICE_URL = "https://service_gacha"
PROFILE_SERVICE_URL = "https://service_profile"
INVENTORY_SERVICE_URL = "https://service_inventory"
SERVICE_TYPE = "gacha"

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


MOCK_PROFILES = {
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": ("JotaroKujo", 5000, 100),
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": ("DIOBrando", 6000, 95),
    "a4f0c592-12af-4bde-aacd-94cd0f27c57e": ("GiornoGiovanna", 4500, 85),
    "b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d": ("JosukeHigashikata", 3500, 80),
    "4f2e8bb5-38e1-4537-9cfa-11425c3b4284": ("SpeedwagonAdmin", 10000, 98),
    "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6": ("AdminUser", 100000000, 999),
}


def gacha_health_check_get():
    return jsonify({"message": "Service operational."}), 200


def get_gacha_info(gacha_uuid):
    """Get information about a specific gacha."""

    # Mocked Auth - Replace with real implementation
    session = ({"uuid": "mock_user_uuid"}, 200)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    # Mocked Input Sanitization - Replace with real implementation
    valid, gacha_uuid = True, gacha_uuid
    if not valid:
        return jsonify({"message": "Invalid input."}), 400

    try:

        @circuit_breaker
        def get_gacha_mock():
            response = get_gacha(session=None, uuid=gacha_uuid)  # Call internal function correctly
            if response[1] != 200:
                if 400 <= response[1] < 500:  # Client error range. This will catch 404 as well
                    return response  # Return the jsonify'd response directly, DON'T re-jsonify it.
                else:  # Server error
                    raise requests.HTTPError(
                        f"Internal service error: {response[1]}",
                        response=type("MockResponse", (object,), {"status_code": response[1]})(),
                    )

            return jsonify(response[0]), 200  # Jsonify only if internal call successful

        returned_value = get_gacha_mock()
        if isinstance(returned_value, tuple):  # If it's a tuple (error from internal service)
            return returned_value  # Unpack and return the jsonify'd error and code as is
        else:  # it's the already made jsonify
            return returned_value

    except requests.HTTPError as e:
        if e.response.status_code == 404:  # Handle 404s specifically
            return jsonify({"error": "Gacha not found"}), 404
        else:
            return jsonify(
                {"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}
            ), 503  # Generic 503 for other HTTP errors
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def pull_gacha(pool_id):
    """Pull a random gacha from a specific pool."""

    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403
    elif user_uuid not in MOCK_PROFILES:
        return jsonify({"error": "User not found"}), 404

    pool_id = sanitize_string_input(pool_id)

    try:

        @circuit_breaker
        def check_pool_exists():
            pool_exists = exists_pool(None, pool_id)[1] == 200
            return jsonify({"exists": pool_exists}), 200 if pool_exists else 404

        pool_exists_response = check_pool_exists()
        if pool_exists_response[1] == 404:
            return jsonify({"error": "Pool not found"}), 404
        elif pool_exists_response[1] == 503:
            return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

        if not pool_exists_response[0].json.get("exists"):
            return jsonify({"error": "Pool not found"}), 404

        @circuit_breaker
        def get_pool_info_mock():
            response = get_pool(None, pool_id)
            if response[1] != 200:
                return response
            return jsonify(response[0].json), 200

        pool_info_response = get_pool_info_mock()
        if pool_info_response[1] != 200:
            return pool_info_response

        pool = pool_info_response[0].json

        user_currency_response = get_mock_user_currency(user_uuid)  # Get user currency

        if user_currency_response[1] != 200:
            return user_currency_response  # Return error if any

        user_currency = user_currency_response[0].json

        if user_currency["currency"] < pool["price"]:  # Correctly access currency
            return jsonify({"error": "Not enough credits"}), 401

        probabilities = [
            pool[prob]
            for prob in ["probability_common", "probability_rare", "probability_epic", "probability_legendary"]
        ]
        roll = random.random()
        cumulative_prob = 0
        selected_index = -1

        for i, prob in enumerate(probabilities):
            cumulative_prob += prob
            if roll <= cumulative_prob:
                selected_index = i
                break

        selected_item = pool["items"][selected_index]
        if not deduct_mock_currency(user_uuid, pool["price"]):
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503

        @circuit_breaker
        def add_to_inventory_mock():
            global MOCK_INVENTORIES
            new_item_uuid = str(uuid.uuid4())
            MOCK_INVENTORIES[new_item_uuid] = (
                user_uuid,
                selected_item,
                datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                1,
                pool["price"],
            )

            response = get_gacha(None, selected_item)
            return response

        response = add_to_inventory_mock()
        return response

    except requests.HTTPError as e:
        if e.reponse.status_code == 404:
            return jsonify({"error": "No pools found"}), 404
        else:
            return jsonify({"error": "Service unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503
    except IndexError:
        return jsonify({"error": "Pool items misconfigured"}), 500


def get_mock_user_currency(user_uuid):
    user_profile = MOCK_PROFILES.get(user_uuid)
    if user_profile:
        # Mimic the original structure of the response
        return jsonify({"currency": user_profile[1]}), 200  # Return currency as JSON with 200 OK

    return jsonify({"error": "User profile not found"}), 404  # Return not found if profile not exists


def deduct_mock_currency(user_uuid, amount):
    if user_uuid in MOCK_PROFILES:
        name, current_currency, other = MOCK_PROFILES[user_uuid]
        new_currency = max(0, current_currency - amount)
        MOCK_PROFILES[user_uuid] = (name, new_currency, other)
        return True
    else:
        return False


def get_pool_info():
    """Returns a list of available gacha pools."""
    # Auth verification (mocked - replace with your actual implementation)
    session = verify_login(connexion.request.headers.get("Authorization"), service_type=SERVICE_TYPE)
    if session[1] != 200:
        return session
    else:
        session = session[0]

    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403

    try:

        @circuit_breaker
        def get_pools():
            # Simulate a POST request to the internal service
            response = list_pools(session=None)  # Call to mocked internal function.  No pool_codename needed here.
            if response[1] != 200:
                if 400 <= response[1] < 500:  # Client Errors
                    return response  # Return directly
                else:  # Server Errors
                    raise requests.HTTPError(
                        f"Internal service error: {response[1]}",
                        response=type("MockResponse", (object,), {"status_code": response[1]})(),
                    )
            return jsonify(response[0]), 200  # Jsonify the data only if it's a 200

        returned_value = get_pools()
        if isinstance(returned_value, tuple):  # If it's a tuple (error from internal)
            return returned_value
        else:
            return returned_value

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({"error": "No pools found"}), 404
        else:
            return jsonify({"error": "Service temporarily unavailable. Please try again later. [HTTPError]"}), 503
    except requests.RequestException:
        return jsonify({"error": "Service unavailable. Please try again later. [RequestError]"}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Service unavailable. Please try again later. [CircuitBreaker]"}), 503


def get_gachas(not_owned=None):  # Added default value for not_owned --> TODO
    """Returns a list of gacha items based on ownership filter."""
    # ... (Implementation using mocked functions - To be filled in later)
    pass  # TODO
