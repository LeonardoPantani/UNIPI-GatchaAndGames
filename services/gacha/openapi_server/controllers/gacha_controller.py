import connexion
import uuid
import bcrypt
import random
import logging

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server import util
from openapi_server.models.rarity_probability import RarityProbability  # noqa: E501

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
feedback_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)
gacha_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

@feedback_circuit_breaker
def post_feedback():  # noqa: E501
    """Invia un feedback.

    Crea un feedback per gli amministratori. # noqa: E501

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]]
    """
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    data = request.get_json()
    if not data or 'string' not in data:
        return jsonify({"error": "The 'string' field is required in the JSON body."}), 400

    string = data['string']
    user_uuid = session['uuid']  # Get UUID directly from session

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    try:
        connection = mysql.connect()
        cursor = connection.cursor()
        cursor.execute(
            'INSERT INTO feedbacks (user_uuid, content) VALUES (UUID_TO_BIN(%s), %s)',
            (user_uuid, string)
        )
        connection.commit()
        return jsonify({"message": "Feedback created successfully"}), 200
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except Exception as e:
        logging.error(f"Error while posting feedback: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@gacha_circuit_breaker
def get_gacha_info(gacha_uuid):  # noqa: E501
    """Shows infos on a gacha.

    Returns infos on a gacha. # noqa: E501
    """
    cursor = None
    conn = None
    try:
        # Get database connection from Flask current_app
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return {"error": "Database connection not initialized"}, 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

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
        
        result = cursor.fetchone()
        if not result:
            return {"error": "Gacha not found"}, 404

        # Create a Gacha object with the retrieved data
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
        return gacha

    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return {"error": "Service unavailable. Please try again later."}, 503
    except Exception as e:
        return {"error": str(e)}, 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@gacha_circuit_breaker
def roll_gacha():  # noqa: E501
    """Esegue una giocata gacha per l'utente loggato.

    Restituisce l'oggetto ottenuto dalla giocata gacha. # noqa: E501

    :rtype: Union[Dict, Tuple[Dict, int], Tuple[Dict, int, Dict[str, str]]]
    """
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403

    user_uuid = session['uuid']

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    try:
        connection = mysql.connect()
        cursor = connection.cursor()

        # Check if user has enough credits for a gacha roll
        cursor.execute(
            'SELECT currency FROM profiles WHERE uuid = UUID_TO_BIN(%s)',
            (user_uuid,)
        )
        result = cursor.fetchone()

        if not result or result[0] < 10:  # Assuming 10 credits are needed for a roll
            return jsonify({"error": "Not enough credits for a gacha roll."}), 400

        # Deduct credits for the gacha roll
        cursor.execute(
            'UPDATE profiles SET currency = currency - 10 WHERE uuid = UUID_TO_BIN(%s)',
            (user_uuid,)
        )

        # Simulate gacha roll (for simplicity, just generate a random UUID as the prize)
        prize_uuid = str(uuid.uuid4())

        # Insert the prize into the user's inventory
        cursor.execute(
            'INSERT INTO inventories (owner_uuid, item_uuid) VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s))',
            (user_uuid, prize_uuid)
        )

        connection.commit()

        return jsonify({"message": "Gacha roll successful", "prize": prize_uuid}), 200
    except CircuitBreakerError:
        logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503
    except Exception as e:
        logging.error(f"Error while performing gacha roll: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
