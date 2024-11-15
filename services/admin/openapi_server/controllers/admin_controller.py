import connexion
import uuid
import bcrypt
from datetime import date

from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server.models.auction import Auction  # noqa: E501
from openapi_server.models.gacha import Gacha  # noqa: E501
from openapi_server.models.get_all_feedbacks200_response_inner import GetAllFeedbacks200ResponseInner  # noqa: E501
from openapi_server.models.pool import Pool  # noqa: E501
from openapi_server.models.user import User  # noqa: E501
from openapi_server import util

from flask import current_app, jsonify, request, make_response, session
from flaskext.mysql import MySQL

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200


def ban_profile(user_uuid):  # noqa: E501
    """Deletes a profile.

    Allows an admin to delete a user's profile. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
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
    """Creates a gacha.

    Allows the creation of a gacha. # noqa: E501

    :param gacha: 
    :type gacha: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
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


def create_pool(pool):  # noqa: E501
    """Creates a pool.

    Allows the creation of a pool. # noqa: E501

    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
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
            query = "INSERT INTO pools (uuid, name, description) VALUES (%s, %s, %s)"
            pool_uuid = str(uuid.uuid4())
            cursor.execute(query, (pool_uuid, pool.name, pool.description))
            connection.commit()
            cursor.close()

            return jsonify({"message": "Pool successfully created.", "pool_uuid": pool_uuid}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Invalid request."}), 400


def delete_gacha(gacha_uuid):  # noqa: E501
    """Deletes a gacha.

    Allows the deletion of a gacha. # noqa: E501

    :param gacha_uuid: 
    :type gacha_uuid: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()

        check_query = "SELECT 1 FROM gachas_types WHERE uuid = %s"
        cursor.execute(check_query, (gacha_uuid,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            return jsonify({"error": "Gacha not found"}), 404

        delete_query = "DELETE FROM gachas_types WHERE uuid = %s"
        cursor.execute(delete_query, (gacha_uuid,))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Gacha successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_pool(pool_id):  # noqa: E501
    """Deletes a pool.

    Allows the deletion of a pool. # noqa: E501

    :param pool_id: 
    :type pool_id: str
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if 'username' not in session or session.get('role') != 'ADMIN':
        return jsonify({"error": "This account is not authorized to perform this action"}), 403
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500

        connection = mysql.connect()
        cursor = connection.cursor()
        query = "DELETE FROM pools WHERE uuid = %s"
        cursor.execute(query, (pool_id,))
        connection.commit()
        cursor.close()

        return jsonify({"message": "Pool successfully deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def edit_user_profile(user_uuid, email=None, username=None):  # noqa: E501
    """Edits properties of a profile.

    Allows an admin to edit a user&#39;s profile. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param session: 
    :type session: str
    :param email: 
    :type email: str
    :param username: 
    :type username: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_all_feedbacks(session=None, page_number=None):  # noqa: E501
    """Returns all feedbacks.

    Allows to retrieve all feedbacks, paginated. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[GetAllFeedbacks200ResponseInner], Tuple[List[GetAllFeedbacks200ResponseInner], int], Tuple[List[GetAllFeedbacks200ResponseInner], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_all_profiles(session=None, page_number=None):  # noqa: E501
    """Returns all profiles.

    Allows to retrieve all profiles, paginated. # noqa: E501

    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_feedback(feedback_id):  # noqa: E501
    """Returns a feedback by id.

    Allows to read a specific feedback. # noqa: E501

    :param feedback_id: Id of feedback.
    :type feedback_id: int
    :param session: 
    :type session: str

    :rtype: Union[str, Tuple[str, int], Tuple[str, int, Dict[str, str]]
    """
    return 'do some magic!'


def get_system_logs(session=None):  # noqa: E501
    """Returns the system logs.

    Allows to retrieve logs of the system. # noqa: E501

    :param session: 
    :type session: str

    :rtype: Union[List[str], Tuple[List[str], int], Tuple[List[str], int, Dict[str, str]]
    """
    return 'do some magic!'


def get_user_history(user_uuid, type, page_number=None):  # noqa: E501
    """Returns history of a user.

    Allows to retrieve history of a user. # noqa: E501

    :param user_uuid: 
    :type user_uuid: str
    :type user_uuid: str
    :param type: Type of history to show.
    :type type: str
    :param session: 
    :type session: str
    :param page_number: Page number of the list.
    :type page_number: int

    :rtype: Union[List[User], Tuple[List[User], int], Tuple[List[User], int, Dict[str, str]]
    """
    return 'do some magic!'


def update_auction(auction_uuid, auction):  # noqa: E501
    """Updates an auction.

    Allows the update of an auction. # noqa: E501

    :param auction_uuid: 
    :type auction_uuid: str
    :type auction_uuid: str
    :param auction: 
    :type auction: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        auction = Auction.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_gacha(gacha_uuid, gacha):  # noqa: E501
    """Updates a gacha.

    Allows the update of a gacha. # noqa: E501

    :param gacha_uuid: 
    :type gacha_uuid: str
    :type gacha_uuid: str
    :param gacha: 
    :type gacha: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        gacha = Gacha.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def update_pool(pool_id, pool):  # noqa: E501
    """Updates a pool.

    Allows the update of a pool. # noqa: E501

    :param pool_id: 
    :type pool_id: str
    :param pool: 
    :type pool: dict | bytes
    :param session: 
    :type session: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if connexion.request.is_json:
        pool = Pool.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
