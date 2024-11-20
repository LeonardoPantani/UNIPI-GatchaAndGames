import connexion
import uuid
import bcrypt
import logging
import requests

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.bundle import Bundle  # noqa: E501
from openapi_server import util

from flask import jsonify, session, current_app
from flaskext.mysql import MySQL

from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

TRANSACTION_TYPE_BUNDLE_CODE = "bought_bundle"
global_mock_accounts = {
    "87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09": {
        "username": "user1",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 100
            },
            {
                "currency": "USD",
                "amount": 300
            }
        ]
    },
    "e3b0c442-98fc-1c14-b39f-92d1282048c0": {
        "username": "user2",
        "accounts": [
            {
                "currency": "USD",
                "amount": 50
            }
        ]
    },
    "16ca8be1-8497-4957-ad5c-ad0bbe2a2863": {
        "username": "user3",
        "accounts": [
            {
                "currency": "EUR",
                "amount": 200
            }
        ]
    }
}

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


@circuit_breaker
def buy_currency(bundle_id):  # noqa: E501
    if 'username' not in session:
        return jsonify({"error": "Not logged in."}), 403

    # valid request

    mysql = current_app.extensions.get('mysql')
    
    try:
        connection = mysql.connect()
        cursor = connection.cursor()
        
        # Get the bundle details from the database
        cursor.execute( #/db_manager/currency/get_bundle_info
            'SELECT * FROM bundles WHERE codename = %s',
            (bundle_id,)
        )
        bundle = cursor.fetchone()

        if not bundle:
            return jsonify({"error": "Bundle not found for the given codename."}), 404

        # Extract bundle data
        codename, currency_name, public_name, credits_obtained, price = bundle

        candidate_user_account_no = -1
        user_accounts = global_mock_accounts.get(session['uuid'])
        for account in user_accounts:
            for index, element in enumerate(account["accounts"]):
                if element["currency"] == currency_name:
                    candidate_user_account_no = index

        if user_accounts["accounts"][candidate_user_account_no]["currency"] != currency_name:
            return jsonify({"error": "Different currency needed, contact your bank."}), 400
        
        if user_accounts["accounts"][candidate_user_account_no]["amount"] < price:
            return jsonify({"error": "You cannot afford this bundle. You poor individual."}), 412
        
        user_accounts["accounts"][candidate_user_account_no]["amount"] -= price

        cursor.execute( #/db_manager/currency/purchase_bundle (credits obtained to send or to leave to the db manager?)
            'UPDATE profiles SET currency = currency + %s WHERE uuid = UUID_TO_BIN(%s)',
            (credits_obtained, session['uuid'])
        )

        cursor.execute(
            'INSERT INTO bundles_transactions (bundle_codename, bundle_currency_name, user_uuid) VALUES (%s, %s, UUID_TO_BIN(%s))',
            (codename, currency_name, session['uuid'])
        )

        cursor.execute(
            'INSERT INTO ingame_transactions (user_uuid, credits, transaction_type) VALUES (UUID_TO_BIN(%s), %s, %s)',
            (session['uuid'], credits_obtained, TRANSACTION_TYPE_BUNDLE_CODE)
        )

        connection.commit()

        return jsonify({"message": "Bundle " + public_name + " successfully bought" }), 200


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

@circuit_breaker
def get_bundles():  # noqa: E501
    try:
        # Establish database connection
        mysql = current_app.extensions.get('mysql')
        
        connection = mysql.connect()
        cursor = connection.cursor()

        # Query to fetch available bundles
        cursor.execute(""" 
            SELECT codename, currency_name, public_name, credits_obtained, price
            FROM bundles
        """) #/db_manager/currency/list_bundles

        # Fetch all rows from the query
        bundle_data = cursor.fetchall()

        if not bundle_data:
            return jsonify({"error": "No bundles found."}), 404

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
