import connexion
import uuid
import bcrypt

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server import util

from flask import jsonify, session, current_app
from flaskext.mysql import MySQL
import logging
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
currency_circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

accounts = {
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": {
        "username": "user1",
        "currency": "EUR",
        "amount": 100
    },
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": {
        "username": "user2",
        "currency": "USD",
        "amount": 50
    },
    "16ca8be1-8497-4957-ad5c-ad0bbe2a2863": {
        "username": "user3",
        "currency": "EUR",
        "amount": 200
    }
}

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

@currency_circuit_breaker
def buy_currency(bundle_id):  # noqa: E501
    # Check if the user is logged in by checking the session
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 403
    
    user_uuid = session['uuid']

    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        connection = mysql.connect()
        cursor = connection.cursor()
        
        # Get the bundle details from the database
        cursor.execute(
            'SELECT * FROM bundles WHERE codename = %s',
            (bundle_id,)
        )
        bundle = cursor.fetchone()

        if not bundle:
            return jsonify({"error": "Bundle not found"}), 404

        # Extract bundle data
        codename, currency_name, public_name, credits_obtained, price = bundle

        user_account = accounts.get(user_uuid)

        if user_account['currency'] != currency_name:
            return jsonify({"error": "Different currency needed, contact your bank"}), 400
        
        if user_account['amount'] < price:
            return jsonify({"error": "Not enough credit to buy bundle"}), 400
        
        user_account['amount'] -= price

        cursor.execute(
            'UPDATE profiles SET currency = currency + %s WHERE uuid = UUID_TO_BIN(%s)',
            (credits_obtained, user_uuid)
        )

        cursor.execute(
            'INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES (%s,%s,UUID_TO_BIN(%s))',
            (codename, currency_name, user_uuid)
        )

        cursor.execute(
            'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, "bought_bundle")',
            (user_uuid, credits_obtained)
        )

        connection.commit()

        connection.commit()

        return jsonify({"message": "Bundle " + public_name + " successfully bought" }), 200

    except CircuitBreakerError:
        #logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Rollback the transaction in case of an error
        if connection:
            connection.rollback()
        
        # Return the error message
        logging.error(f"Unexpected error during buy_currency: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

@currency_circuit_breaker
def get_bundles():  # noqa: E501
    try:
        # Establish database connection
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        # Query to fetch available bundles
        cursor.execute("""
            SELECT codename, currency_name, public_name, credits_obtained, price
            FROM bundles
        """)

        # Fetch all rows from the query
        bundle_data = cursor.fetchall()

        if not bundle_data:
            return jsonify({"error": "No bundles found"}), 404

        # Format the bundles data to match the API response structure
        bundles = []
        for bundle in bundle_data:
            codename, currency_name, public_name, credits_obtained, price = bundle
            bundles.append({
                "id": codename,
                "name": public_name,
                "amount": credits_obtained,
                "prices": [
                    {"name": currency_name, "value": price}
                ]
            })

        return jsonify(bundles), 200

    except CircuitBreakerError:
        #logging.error("Circuit Breaker Open: Timeout not elapsed yet, circuit breaker still open.")
        return jsonify({"error": "Service unavailable. Please try again later."}), 503

    except Exception as e:
        # Handle errors and rollback if any database operation failed
        if connection:
            connection.rollback()
       # logging.error(f"Unexpected error during get_bundles: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Close the database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()
