import logging
import connexion
import uuid
import bcrypt
import json
from datetime import date

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.feedback import Feedback  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, session
from flaskext.mysql import MySQL
from pybreaker import CircuitBreaker, CircuitBreakerError



def admin_health_check_get():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


def ban_profile(user_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if session.get('uuid') == user_uuid:
        return jsonify({"error": "You cannot delete your account like this"}), 406
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        query = "SELECT role FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (user_uuid,))
        result = cursor.fetchone()
        if result:
            user_to_ban_role = result[0]
            if user_to_ban_role == "ADMIN":
                return jsonify({"error": "Cannot ban a user with the ADMIN role."}), 409
        else:
            return jsonify({"error": "User not found"}), 404
        
        cursor.execute('DELETE FROM feedbacks WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))
        cursor.execute('DELETE FROM ingame_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,)) 
        cursor.execute('DELETE FROM bundles_transactions WHERE user_uuid = UUID_TO_BIN(%s)', (user_uuid,))

        cursor.execute('''
                        UPDATE profiles SET currency = currency + (
                            SELECT current_bid
                            FROM auctions
                            WHERE item_uuid IN (
                                SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                            )
                        )
                        WHERE uuid IN (
                            SELECT current_bidder
                            FROM auctions
                            WHERE item_uuid IN (
                                SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)
                            )
                        )
                        ''',
                        (user_uuid, user_uuid)
        )
        
        cursor.execute('DELETE FROM pvp_matches WHERE player_1_uuid = UUID_TO_BIN(%s) OR player_2_uuid = UUID_TO_BIN(%s)', (user_uuid,user_uuid))
        cursor.execute('DELETE FROM auctions WHERE item_uuid IN (SELECT item_uuid FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s))', (user_uuid,))
        cursor.execute('DELETE FROM inventories WHERE owner_uuid = UUID_TO_BIN(%s)', (user_uuid,))

        query = "DELETE FROM profiles WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (user_uuid,))

        query = "DELETE FROM users WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (user_uuid,))

        connection.commit()
        cursor.close()

        return jsonify({"message": "Profile successfully banned."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def create_gacha():  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    # valid request from now on
    gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        # converting letters to numbers for storage
        letters_map = {
            'A': 5,
            'B': 4,
            'C': 3,
            'D': 2,
            'E': 1
        }
        attributes = ['power', 'speed', 'durability', 'precision', 'range', 'potential']
        converted = {}
        for attr in attributes:
            letter = getattr(gacha.attributes, attr)
            if letter in letters_map:
                converted[attr] = letters_map[letter]
            else:
                converted[attr] = None
        # converted is a map with for each key (stat) a value (numeric of the stat)

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "INSERT INTO gachas_types (uuid, name, stat_power, stat_speed, stat_durability, stat_precision, stat_range, stat_potential, rarity, release_date) VALUES (UUID_TO_BIN(%s), %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (gacha.gacha_uuid, gacha.name, converted["power"], converted["speed"], converted["durability"], converted["precision"], converted["range"], converted["potential"], gacha.rarity, date.today()))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "The provided gacha uuid is already in use."}), 404
        
        connection.commit()

        return jsonify({"message": "Gacha successfully created.", "gacha_uuid": gacha_uuid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_gacha(gacha_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        delete_query = "DELETE FROM gachas_types WHERE uuid = %s"
        cursor.execute(delete_query, (gacha_uuid,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Gacha not found."}), 404

        cursor.close()

        return jsonify({"message": "Gacha successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_pool():  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501

    # check if probabilities are inside the probabilities fields and are floats
    if not isinstance(pool.probabilities.legendary_probability, float) or not isinstance(pool.probabilities.rare_probability, float) or not isinstance(pool.probabilities.epic_probability, float) or not isinstance(pool.probabilities.common_probability, float):
        return jsonify({"error": "Invalid probabilities field."}), 412
    
    # check if sum of probabilities is 1
    if pool.probabilities.legendary_probability + pool.probabilities.epic_probability + pool.probabilities.rare_probability + pool.probabilities.common_probability != 1:
        return jsonify({"error": "Sum of probabilities is not 1."}), 416
    
    if pool.price < 1:
        return jsonify({"error": "Price should be a positive number."}), 416

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500   

        connection = mysql.connect()
        cursor = connection.cursor()
        
        # checks ok, inserting
        try:
            probabilities = {
                "common_probability": pool.probabilities.common_probability,
                "rare_probability": pool.probabilities.rare_probability,
                "epic_probability": pool.probabilities.epic_probability,
                "legendary_probability":  pool.probabilities.legendary_probability,
            }
            query = "INSERT INTO gacha_pools (codename, public_name, probabilities, price) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (pool.id, pool.name, json.dumps(probabilities), pool.price))
            connection.commit()
            cursor.close()
        except mysql.connect().IntegrityError:
            # Duplicate pool codename error
            connection.rollback()
            return jsonify({"error": "The provided pool id is already in use."}), 409

        return jsonify({"message": "Pool successfully created."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def delete_pool(pool_id):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "DELETE FROM gacha_pools WHERE codename = %s"
        cursor.execute(query, (pool_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Pool not found."}), 404

        cursor.close()

        return jsonify({"message": "Pool successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def edit_user_profile(user_uuid, email=None, username=None):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if profile with that uuid exists
        query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (user_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "User not found."}), 404

        # user exists, continue
        updates = 0

        if email:
            query = "UPDATE users SET email = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (email, user_uuid))
            updates += cursor.rowcount
        if username:
            query = "UPDATE profiles SET username = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (username, user_uuid))
            updates += cursor.rowcount
        connection.commit()

        if updates == 0:
            cursor.close()
            return jsonify({"error": "No changes to profile applied."}), 304
        
        cursor.close()

        return jsonify({"message": "User profile successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def get_all_feedbacks(page_number=None):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        offset = (page_number - 1) * 10 if page_number else 0
        query = "SELECT f.id, BIN_TO_UUID(f.user_uuid), f.timestamp FROM feedbacks f LIMIT 10 OFFSET %s"
        cursor.execute(query, (offset,))
        feedbacks = cursor.fetchall()
        cursor.close()

        feedback_list = [
            {"id": feedback[0], "user_uuid": feedback[1], "timestamp": str(feedback[2])}
            for feedback in feedbacks
        ]
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_all_profiles(page_number=None):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        offset = (page_number - 1) * 10 if page_number else 0
        query = "SELECT BIN_TO_UUID(p.uuid) as uuid, u.email, p.username, p.currency, p.pvp_score, p.created_at, u.role FROM profiles p JOIN users u ON p.uuid = u.uuid LIMIT 10 OFFSET %s"
        cursor.execute(query, (offset,))
        profiles = cursor.fetchall()
        cursor.close()

        profile_list = [
            {"id": profile[0], "email": profile[1], "username": profile[2], "currency": profile[3], "pvp_score": profile[4], "joindate": str(profile[5]), "role": profile[6]}
            for profile in profiles
        ]
        return jsonify(profile_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_feedback_info(feedback_id):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "SELECT f.id, BIN_TO_UUID(f.user_uuid) as uuid, f.content, f.timestamp, p.username FROM feedbacks f JOIN profiles p ON f.user_uuid = p.uuid WHERE id = %s"
        cursor.execute(query, (feedback_id,))
        feedback = cursor.fetchone()
        cursor.close()

        if feedback:
            feedback_info = {"id": feedback[0], "user_uuid": feedback[1], "content": feedback[2], "timestamp": feedback[3], "username": feedback[4]}
            return jsonify(feedback_info), 200
        else:
            return jsonify({"error": "Feedback not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_system_logs():  # noqa: E501 TODO
    return 'do some magic!'


def get_user_history(user_uuid, history_type, page_number=None):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if profile with that uuid exists
        query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (user_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "User not found."}), 404

        # user exists, continue
        offset = (page_number - 1) * 10 if page_number else 0

        if history_type == 'ingame':
            query = "SELECT BIN_TO_UUID(t.user_uuid) as user_uuid, t.credits, t.transaction_type, t.timestamp, p.username FROM ingame_transactions t JOIN profiles p ON t.user_uuid = p.uuid WHERE t.user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
        elif history_type == 'bundle':
            query = "SELECT BIN_TO_UUID(t.user_uuid) as user_uuid, t.bundle_codename, t.bundle_currency_name, t.timestamp, p.username FROM bundles_transactions t JOIN profiles p ON t.user_uuid = p.uuid WHERE t.user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
        else:
            return jsonify({"error": "Invalid history type."}), 405
        
        cursor.execute(query, (user_uuid, offset))
        history = cursor.fetchall()
        cursor.close()

        if history_type == "ingame":
            history_list = [
                {"user_uuid": entry[0], "credits": entry[1], "transaction_type": entry[2], "timestamp": str(entry[3]), "username": entry[4]}
                for entry in history
            ]
        else: # history_type == bundle
            history_list = [
                {"user_uuid": entry[0], "codename": entry[1], "currency_name": entry[2], "timestamp": str(entry[3]), "username": entry[4]}
                for entry in history
            ]
        return jsonify(history_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_auction(auction_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    
    auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    
    if auction.auction_uuid != auction_uuid:
        return jsonify({"message": "Auction UUID in request is different from the one inside the auction object."}), 406
    
    # starting price check
    if auction.starting_price <= 0:
        return jsonify({"error": "Starting price cannot be lower or equal to 0."}), 412
    
    # starting price check
    if auction.current_bid < 0:
        return jsonify({"error": "Current bid cannot be lower than 0."}), 416
    
    # Current bid cannot be lower than starting price
    if auction.current_bid < auction.starting_price:
        return jsonify({"error": "Current bid cannot be lower than starting price."}), 401
    

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if auction with that uuid exists
        query = "SELECT uuid FROM auctions WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Auction not found"}), 404

        # check if item with that uuid exists
        query = "SELECT item_uuid FROM inventories WHERE item_uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction.inventory_item_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Item ID not found in any inventory"}), 404

        # check if current bidder is a valid user uuid
        query = "SELECT uuid FROM users WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (auction.current_bidder,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Current bidder user profile not found"}), 404

        # auction exists, continue
        query = "UPDATE auctions SET item_uuid = UUID_TO_BIN(%s), starting_price = %s, current_bid = %s, current_bidder = UUID_TO_BIN(%s), end_time = %s WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (auction.inventory_item_id, auction.starting_price, auction.current_bid, auction.current_bidder, auction.end_time, auction_uuid))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Auction successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def update_gacha(gacha_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501

    if gacha.gacha_uuid != gacha_uuid:
        return jsonify({"message": "Gacha UUID in request is different from the one inside the gacha object."}), 406
    
    # check if stats have correct rating and create a map with converted letters to number ratings
    letters_map = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1
    }
    attributes = ['power', 'speed', 'durability', 'precision', 'range', 'potential']
    converted = {}
    for attr in attributes:
        letter = getattr(gacha.attributes, attr)
        if letter in letters_map:
            converted[attr] = letters_map[letter]
        else: # no valid letter found
            converted[attr] = None
    # converted is a map with for each key (stat) a value (numeric of the stat)

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        # check if gacha with that uuid exists
        query = "SELECT uuid FROM gachas_types WHERE uuid = UUID_TO_BIN(%s) LIMIT 1"
        cursor.execute(query, (gacha_uuid,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Gacha not found."}), 404
        

        query = "UPDATE gachas_types SET name = %s, stat_power = %s, stat_speed = %s, stat_durability = %s, stat_precision = %s, stat_range = %s, stat_potential = %s, rarity = %s WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (gacha.name, converted["power"], converted["speed"], converted["durability"], converted["precision"], converted["range"], converted["potential"], gacha.rarity, gacha.gacha_uuid))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Gacha successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500


def update_pool(pool_id):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501

    if pool.id != pool_id:
        return jsonify({"message": "Pool UUID in request is different from the one inside the pool object."}), 406

    # check if probabilities are inside the probabilities fields and are floats
    if not isinstance(pool.probabilities.legendary_probability, float) or not isinstance(pool.probabilities.rare_probability, float) or not isinstance(pool.probabilities.epic_probability, float) or not isinstance(pool.probabilities.common_probability, float):
        return jsonify({"error": "Invalid probabilities field."}), 412
    
    # check if sum of probabilities is 1
    if pool.probabilities.legendary_probability + pool.probabilities.epic_probability + pool.probabilities.rare_probability + pool.probabilities.common_probability != 1:
        return jsonify({"error": "Sum of probabilities is not 1."}), 416

    if pool.price < 1:
        return jsonify({"error": "Price should be a positive number."}), 416

    # valid request from now on
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
        
        connection = mysql.connect()
        cursor = connection.cursor()

        probabilities = {
            "common_probability": pool.probabilities.common_probability,
            "rare_probability": pool.probabilities.rare_probability,
            "epic_probability": pool.probabilities.epic_probability,
            "legendary_probability":  pool.probabilities.legendary_probability,
        }
        query = "UPDATE gacha_pools SET public_name = %s, probabilities = %s, price = %s WHERE codename = %s"
        cursor.execute(query, (pool.name, json.dumps(probabilities), pool.price, pool_id))
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Pool not found."}), 404
        
        cursor.close()

        return jsonify({"message": "Pool successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500