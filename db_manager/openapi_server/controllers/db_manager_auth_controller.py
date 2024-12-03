import connexion
from flask import jsonify
from mysql.connector.errors import (
    OperationalError,
    DataError,
    DatabaseError,
    IntegrityError,
    InterfaceError,
    InternalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError
from openapi_server.helpers.logging import send_log
from openapi_server.helpers.db import get_db

circuit_breaker = CircuitBreaker(
    fail_max=3,
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


def login():
    if not connexion.request.is_json:
        return "", 400

    # valid json request
    login_request = connexion.request.get_json()
    username = login_request.get("username")

    try:

        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            query = """
                SELECT BIN_TO_UUID(u.uuid), u.uuid, u.email, p.username, u.role, u.password
                FROM users u
                JOIN profiles p ON u.uuid = p.uuid
                WHERE p.username = %s
            """
            cursor.execute(query, (username,))
            return cursor.fetchone()

        result = make_request_to_db()

        if result:
            user_uuid_str, user_uuid_hex, user_email, user_name, user_role, user_password = result
            payload = {
                "uuid": user_uuid_str,
                "uuid_hex": str(user_uuid_hex),
                "email": user_email,
                "username": user_name,
                "role": user_role,
                "password": user_password,
            }
            return jsonify(payload), 200
        else:
            return "", 404
    except OperationalError:
        logging.error("Query [" + username + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query [" + username + "]: Programming error.")
        return "", 500
    except InternalError:
        logging.error("Query [" + username + "]: Internal error.")
        return "", 500
    except InterfaceError as e:
        logging.error("Query [" + username + "]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query [" + username + "]: Database error.")
        return "", 500
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503


def register():
    if not connexion.request.is_json:
        return "", 400

    # valid json request
    login_request = connexion.request.get_json()
    user_uuid = login_request.get("uuid")
    username = login_request.get("username")
    email = login_request.get("email")
    password_hash = login_request.get("password")
    role = login_request.get("role")

    connection = None
    try:

        @circuit_breaker
        def make_request_to_db():
            connection = get_db()
            cursor = connection.cursor()
            # Insert user in USERS table
            cursor.execute(
                "INSERT INTO users (uuid, email, password, role) VALUES (UUID_TO_BIN(%s), %s, %s, %s)",
                (user_uuid, email, password_hash, role),
            )
            # Insert profile in PROFILE table
            cursor.execute(
                "INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES (UUID_TO_BIN(%s), %s, %s, %s)",
                (user_uuid, username, 0, 0),
            )
            connection.commit()
            return

        make_request_to_db()
        return "", 201
    except OperationalError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Operational error.")
        return "", 500
    except ProgrammingError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Programming error.")
        return "", 500
    except IntegrityError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError:  # if data format is invalid or out of range or size
        logging.error("Query [" + user_uuid + ", " + username + "]: Data error.")
        return "", 500
    except InternalError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Internal error.")
        return "", 500
    except InterfaceError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Interface error.")
        return "", 500
    except DatabaseError:
        logging.error("Query [" + user_uuid + ", " + username + "]: Database error.")
        return "", 401
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
