############# WARNING #############
#   !   This is a mock file.  !   #
###################################
import string

import connexion
import jwt
import requests
from flask import current_app, jsonify
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

from openapi_server.helpers.authorization import MOCK_REDIS
from openapi_server.helpers.logging import send_log
from openapi_server.models.introspect_request import IntrospectRequest
from openapi_server.models.userinfo_request import UserinfoRequest

MOCK_TABLE_USERS = [
    (
        "e3b0c442-98fc-1c14-b39f-92d1282048c0",
        "jotaro@joestar.com",
        "$2b$12$XRQfYzKIQoyQXNUYU0lcB.p/YHN5YqXxEn62BH5WiK.w8Q.i5z7cy",
        "USER",
    ),  # password: star_platinum
    (
        "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09",
        "dio.brando@world.com",
        "$2a$12$YUKGEXCU2rGtqnkeStuL6.3SA5IIsBdAC9qv9mrXm4Pa/mLIYPu/K",
        "USER",
    ),  # password: za_warudo
    (
        "a4f0c592-12af-4bde-aacd-94cd0f27c57e",
        "giorno@passione.it",
        "$2b$12$jqb2pkG1hQ4j4xJkbYTt8el9iVraf9IOg5ODWR9cjHcVF9sttNTja",
        "USER",
    ),  # password: gold_experience
    (
        "b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d",
        "josuke@morioh.jp",
        "$2a$12$4N3oX0NTo5ccUZmCBpCx/uSe14rtSd1E/sZhbOK2eclfQ3o.gdHCa",
        "USER",
    ),  # password: crazy_diamond
    (
        "4f2e8bb5-38e1-4537-9cfa-11425c3b4284",
        "speedwagon@foundation.org",
        "$2a$12$9HgqzV4s6zhKCBFRMuUGSONqS2bhIQqzpiF1U/K/VW1ofYWyU2mIa",
        "ADMIN",
    ),  # password: admin_foundation
    (
        "a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6",
        "admin@admin.com",
        "$2a$12$Io8F/0QZ8hLSZ.CtqUvM0uK/jhmdXohCFXiby/nHk3ePmzNf1wRhe",
        "ADMIN",
    ),  # password: password
]

MOCK_TABLE_PROFILES = [
    ("e3b0c442-98fc-1c14-b39f-92d1282048c0", "JotaroKujo", 5000, 100),
    ("87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09", "DIOBrando", 6000, 95),
    ("a4f0c592-12af-4bde-aacd-94cd0f27c57e", "GiornoGiovanna", 4500, 85),
    ("b5c3d2e1-4f5e-6a7b-8c9d-0e1f2a3b4c5d", "JosukeHigashikata", 3500, 80),
    ("4f2e8bb5-38e1-4537-9cfa-11425c3b4284", "SpeedwagonAdmin", 10000, 98),
    ("a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6", "AdminUser", 100000000, 999),
]


SERVICE_TYPE = "auth"
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


def introspect(introspect_request=None):
    """
    The object must be { "access_token": "eyJhbGciOiJIUzI1NiIsInR5...", "audience_required": "public_services"/"private_services" }
    This decrypts your access token and checks with REDIS that it is the same one saved by the user with the uuid written inside the token.
    """
    if not connexion.request.is_json:  # checks if the request is a correct json
        return "", 400

    introspect_request = IntrospectRequest.from_dict(connexion.request.get_json())
    if not introspect_request.access_token or not introspect_request.audience_required:
        return "", 400

    if (
        introspect_request.audience_required != "public_services"
        and introspect_request.audience_required != "private_services"
    ):
        return "", 400

    try:
        decoded_token = jwt.decode(
            introspect_request.access_token,
            current_app.config["jwt_secret_key"],
            algorithms=["HS256"],
            audience=introspect_request.audience_required,
        )
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"],
        }

        # obtaining token saved in Redis
        if decoded_token["uuid"] in MOCK_REDIS:
            saved_token = MOCK_REDIS[decoded_token["uuid"]]
        else:
            send_log("Redis error", level="error", service_type=SERVICE_TYPE)
            return jsonify({"error": "Service unavailable. Please try again later."}), 503

        # if no token is saved probably is because Redis was restarted since user logged in
        if saved_token is None:
            send_log(
                f"Token for user {decoded_token["username"]} is valid but was not found in Redis.",
                level="warning",
                service_type=SERVICE_TYPE,
            )
            return jsonify({"error": "Unauthorized."}), 401

        # if it is not equal to the one saved in Redis, it is a problem
        if saved_token != introspect_request.access_token:
            send_log(
                f"Saved token for '{decoded_token["username"]}' is not the same as the saved one in Redis.",
                level="info",
                service_type=SERVICE_TYPE,
            )
            return jsonify({"error": "Unauthorized."}), 401

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired."}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Unauthorized."}), 401


def userinfo(userinfo_request=None):
    """
    The object must be { "access_token": "eyJhbGciOiJIUzI1NiIsInR5..." }
    This function just decrypts your access_token, without any further checks.
    """
    if not connexion.request.is_json:
        return "", 400

    userinfo_request = UserinfoRequest.from_dict(connexion.request.get_json())
    if not userinfo_request.access_token:
        return "", 400

    try:
        decoded_token = jwt.decode(
            userinfo_request.access_token,
            current_app.config["jwt_secret_key"],
            algorithms=["HS256"],
            audience="public_services",
        )
        result = {
            "email": decoded_token["email"],
            "username": decoded_token["username"],
            "uuid": decoded_token["uuid"],
            "uuidhex": decoded_token["uuidhex"],
            "role": decoded_token["role"],
            "logindate": decoded_token["logindate"],
        }

        return result, 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 402
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


def delete_user_by_uuid(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400

    try:

        @circuit_breaker
        def delete_user():
            global MOCK_TABLE_USERS
            initial_length = len(MOCK_TABLE_USERS)
            MOCK_TABLE_USERS = [user for user in MOCK_TABLE_USERS if user[0] != uuid]
            return len(MOCK_TABLE_USERS) < initial_length

        user_deleted = delete_user()

        if not user_deleted:
            return jsonify({"error": "User not found."}), 404

        return jsonify({"message": "User deleted."}), 200

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: delete_user", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def edit_email(session=None, uuid=None, email=None):
    if not uuid or not email:
        return jsonify({"error": "Invalid request."}), 400

    # Verifying if user exists
    try:

        @circuit_breaker
        def verify_user_exists():
            return find_user_by_uuid(uuid) is not None

        user_exists = verify_user_exists()

        if not user_exists:
            return jsonify({"error": "User not found."}), 404

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: verify_user_exists", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503

    # Updating email
    try:

        @circuit_breaker
        def update_email():
            for idx, user in enumerate(MOCK_TABLE_USERS):
                if user[0] == uuid:
                    if user[1] == email:
                        return False
                    else:
                        MOCK_TABLE_USERS[idx] = (user[0], email, user[2], user[3])
                        return True

        email_updated = update_email()

        if not email_updated:
            return jsonify({"error": "No changes applied."}), 304

        return jsonify({"message": "Email updated."}), 200

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: update_email", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def get_hashed_password(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400

    try:

        @circuit_breaker
        def get_password():
            return get_user_password(uuid)

        password = get_password()

        if not password:
            return jsonify({"error": "User not found."}), 404

        return jsonify({"password": password}), 200

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: get_password", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def get_role_by_uuid(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400

    try:

        @circuit_breaker
        def get_role():
            return get_user_role(uuid)

        role = get_role()

        if not role:
            return jsonify({"error": "User not found."}), 404

        return jsonify({"role": role.upper()}), 200

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: get_role", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


def get_user(session=None, uuid=None):
    if not uuid:
        return jsonify({"error": "Invalid request."}), 400

    try:

        @circuit_breaker
        def fetch_user():
            user = find_user_by_uuid(uuid)
            if user:
                return {"uuid": user[0], "email": user[1], "role": user[3].upper()}
            return None

        result = fetch_user()

        if not result:
            return jsonify({"error": "User not found."}), 404

        return jsonify(result), 200

    except CircuitBreakerError:
        send_log("CircuitBreaker Error: fetch_user", level="warning", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503


# mock
def find_user_by_uuid(uuid):
    return next((user for user in MOCK_TABLE_USERS if user[0] == uuid), None)


def get_user_role(uuid):
    user = find_user_by_uuid(uuid)
    return user[3] if user else None


def get_user_password(uuid):
    user = find_user_by_uuid(uuid)
    return user[2] if user else None
