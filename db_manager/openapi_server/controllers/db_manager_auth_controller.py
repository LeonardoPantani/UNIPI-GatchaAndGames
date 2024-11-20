import connexion
import logging
from flask import current_app, jsonify
from pymysql.err import OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError
from pybreaker import CircuitBreaker, CircuitBreakerError


# circuit breaker to stop requests when dbmanager fails
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])





def login():
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    login_request = connexion.request.get_json()
    username = login_request.get("username")

    mysql = current_app.extensions.get('mysql')

    connection = None
    cursor = None
    try:
        @circuit_breaker
        def make_request_to_db():
            # Query the database for user based on username in PROFILE and hash in USERS
            connection = mysql.connect()
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
                "password": user_password
            }
            return jsonify(payload), 200
        else:
            return jsonify({"error": "Invalid username."}), 404
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ username +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ username +"]: Programming error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ username +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ username +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ username +"]: Database error.")
        return "", 500
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503
    finally:
        if connection:
            connection.close()
        if cursor:
            cursor.close()


def register():
    if not connexion.request.is_json:
        return "", 400
    
    # valid json request
    login_request = connexion.request.get_json()
    user_uuid = login_request.get("uuid")
    username = login_request.get("username")
    email = login_request.get("email")
    password_hash = login_request.get("password")

    mysql = current_app.extensions.get('mysql')
    connection = None
    try:
        @circuit_breaker
        def make_request_to_db():
            connection = mysql.connect()
            cursor = connection.cursor()
            # Insert user in USERS table
            cursor.execute(
                'INSERT INTO users (uuid, email, password, role) VALUES (UUID_TO_BIN(%s), %s, %s, %s)',
                (user_uuid, email, password_hash, 'USER')
            )
            # Insert profile in PROFILE table
            cursor.execute(
                'INSERT INTO profiles (uuid, username, currency, pvp_score) VALUES (UUID_TO_BIN(%s), %s, %s, %s)',
                (user_uuid, username, 0, 0)
            )
            connection.commit()
            return

        make_request_to_db()
        return "", 201
    except OperationalError: # if connect to db fails means there is an error in the db
        logging.error("Query ["+ user_uuid +", "+ username +"]: Operational error.")
        return "", 500
    except ProgrammingError: # for example when you have a syntax error in your SQL or a table was not found
        logging.error("Query ["+ user_uuid +", "+ username +"]: Programming error.")
        return "", 400
    except IntegrityError: # for constraint violations such as duplicate entries or foreign key constraints
        logging.error("Query ["+ user_uuid +", "+ username +"]: Integrity error.")
        if connection:
            connection.rollback()
        return "", 409
    except DataError: # if data format is invalid or out of range or size
        logging.error("Query ["+ user_uuid +", "+ username +"]: Data error.")
        return "", 400
    except InternalError: # when the MySQL server encounters an internal error, for example, when a deadlock occurred
        logging.error("Query ["+ user_uuid +", "+ username +"]: Internal error.")
        return "", 500
    except InterfaceError: # errors originating from Connector/Python itself, not related to the MySQL server
        logging.error("Query ["+ user_uuid +", "+ username +"]: Interface error.")
        return "", 500
    except DatabaseError: # default for any MySQL error which does not fit the other exceptions
        logging.error("Query ["+ user_uuid +", "+ username +"]: Database error.")
        return "", 401
    except CircuitBreakerError: # if request already failed multiple times, the circuit breaker is open and this code gets executed
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return "", 503