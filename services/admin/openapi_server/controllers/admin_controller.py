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

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def ban_profile(user_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if session.get('uuid') == user_uuid:
        return jsonify({"error": "You cannot delete your account like this"}), 400
    
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
                return jsonify({"error": "Cannot ban a user with the ADMIN role"}), 409
        else:
            return jsonify({"error": "User not found"}), 404

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
    
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500

            # Conversione lettere a numeri per lo storage
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
            gacha_uuid = uuid.uuid4()
            cursor.execute(query, (gacha_uuid, gacha.name, converted["power"], converted["speed"], converted["durability"], converted["precision"], converted["range"], converted["potential"], gacha.rarity, date.today()))
            connection.commit()
            cursor.close()

            return jsonify({"message": "Gacha successfully created.", "gacha_uuid": gacha_uuid}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400

def delete_gacha(gacha_uuid):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
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
    
    if connexion.request.is_json:
        pool = connexion.request.get_json()  # noqa: E501
        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500
            
            # check if probabilities are inside the probabilities fields and are floats
            if not isinstance(pool.get("probabilities").get("legendaryProbability"), float) or not isinstance(pool.get("probabilities").get("rareProbability"), float) or not isinstance(pool.get("probabilities").get("epicProbability"), float) or not isinstance(pool.get("probabilities").get("commonProbability"), float):
                return jsonify({"error": "Invalid probabilities field."}), 500      

            connection = mysql.connect()
            cursor = connection.cursor()

            # check if items really exists
            for item in pool.get("items"):
                query = "SELECT uuid FROM gachas_types WHERE uuid = UUID_TO_BIN(%s)"
                cursor.execute(query, (item))
                connection.commit()
                tocheck = cursor.fetchone()
                if tocheck is None:
                    return jsonify({"error": "Item UUID not found in database: " + item}), 400
            
            # checks ok, inserting
            try:
                query = "INSERT INTO gacha_pools (codename, public_name, probabilities, items) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (pool.get("id"), pool.get("name"), json.dumps(pool.get("probabilities")), json.dumps(pool.get("items"))))
                connection.commit()
                cursor.close()
            except mysql.connect().IntegrityError:
                # Duplicate email error
                connection.rollback()
                return jsonify({"error": "The provided pool id is already in use."}), 409

            return jsonify({"message": "Pool successfully created."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400

def delete_pool(pool_id):  # noqa: E501
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
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

def edit_user_profile(user_uuid, email=None, username=None):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        if email:
            query = "UPDATE users SET email = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (email, user_uuid))
        if username:
            query = "UPDATE profiles SET username = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (username, user_uuid))
        
        connection.commit()
        cursor.close()

        return jsonify({"message": "User profile successfully updated."}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

def get_all_feedbacks(page_number=None):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        offset = (page_number - 1) * 10 if page_number else 0
        query = "SELECT BIN_TO_UUID(uuid), feedback_text, rating FROM feedbacks LIMIT 10 OFFSET %s"
        cursor.execute(query, (offset,))
        feedbacks = cursor.fetchall()
        cursor.close()

        feedback_list = [
            {"uuid": feedback[0], "feedback_text": feedback[1], "rating": feedback[2]}
            for feedback in feedbacks
        ]
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_all_profiles(page_number=None):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        offset = (page_number - 1) * 10 if page_number else 0
        query = "SELECT BIN_TO_UUID(uuid), username, currency, pvp_score FROM profiles LIMIT 10 OFFSET %s"
        cursor.execute(query, (offset,))
        profiles = cursor.fetchall()
        cursor.close()

        profile_list = [
            {"uuid": profile[0], "username": profile[1], "currency": profile[2], "pvp_score": profile[3]}
            for profile in profiles
        ]
        return jsonify(profile_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_feedback_info(feedback_uuid):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "SELECT BIN_TO_UUID(uuid), feedback_text, rating FROM feedbacks WHERE uuid = UUID_TO_BIN(%s)"
        cursor.execute(query, (feedback_uuid,))
        feedback = cursor.fetchone()
        cursor.close()

        if feedback:
            feedback_info = {"uuid": feedback[0], "feedback_text": feedback[1], "rating": feedback[2]}
            return jsonify(feedback_info), 200
        else:
            return jsonify({"error": "Feedback not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_system_logs():  # noqa: E501 TODO
    return 'do some magic!'

def get_user_history(user_uuid, type, page_number=None):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        offset = (page_number - 1) * 10 if page_number else 0

        if type == 'auction':
            query = "SELECT BIN_TO_UUID(uuid), item_name, bid_amount, status FROM auctions WHERE user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
        elif type == 'gacha':
            query = "SELECT BIN_TO_UUID(uuid), gacha_name, result, status FROM gachas WHERE user_uuid = UUID_TO_BIN(%s) LIMIT 10 OFFSET %s"
        else:
            return jsonify({"error": "Invalid history type"}), 400
        
        cursor.execute(query, (user_uuid, offset))
        history = cursor.fetchall()
        cursor.close()

        history_list = [
            {"uuid": entry[0], "name": entry[1], "result": entry[2], "status": entry[3]}
            for entry in history
        ]
        return jsonify(history_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_auction(auction_uuid, auction):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500

            connection = mysql.connect()
            cursor = connection.cursor()
            query = "UPDATE auctions SET item_name = %s, bid_amount = %s, status = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (auction.item_name, auction.bid_amount, auction.status, auction_uuid))
            connection.commit()
            cursor.close()

            return jsonify({"message": "Auction successfully updated."}), 200
        except Exception as e:
            connection.rollback()
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400

def update_gacha(gacha_uuid, gacha):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500

            connection = mysql.connect()
            cursor = connection.cursor()
            query = "UPDATE gachas_types SET name = %s, stat_power = %s, stat_speed = %s, stat_durability = %s, stat_precision = %s, stat_range = %s, stat_potential = %s, rarity = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (gacha.name, gacha.stat_power, gacha.stat_speed, gacha.stat_durability, gacha.stat_precision, gacha.stat_range, gacha.stat_potential, gacha.rarity, gacha_uuid))
            connection.commit()
            cursor.close()

            return jsonify({"message": "Gacha successfully updated."}), 200
        except Exception as e:
            connection.rollback()
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400

def update_pool(pool_id, pool):  # noqa: E501 TODO
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
        try:
            mysql = current_app.extensions.get('mysql')
            if not mysql:
                return jsonify({"error": "Database connection not initialized"}), 500

            connection = mysql.connect()
            cursor = connection.cursor()
            query = "UPDATE pools SET name = %s, description = %s WHERE uuid = UUID_TO_BIN(%s)"
            cursor.execute(query, (pool.name, pool.description, pool_id))
            connection.commit()
            cursor.close()

            return jsonify({"message": "Pool successfully updated."}), 200
        except Exception as e:
            connection.rollback()
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400