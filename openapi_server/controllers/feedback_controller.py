import connexion
import uuid
from typing import Dict
from typing import Tuple
from typing import Union

from flask import jsonify, current_app, session

from openapi_server import util


def post_feedback():  # noqa: E501
    """Sends a feedback.

    Creates a feedback to the admins. # noqa: E501

    :param session: 
    :type session: str
    :param string: 
    :type string: str

    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """

    # Obtaining cookie session and feedback string
    session = connexion.request.cookies.get("session")
    string = connexion.request.args.get("string")
    
    # Checking session cookie validity
    if not session or len(session) != 20:
        return jsonify({"error": "Invalid or missing session cookie"}), 400
    
    # Check if the string is not empty and less than 65000 characters long
    if not string or len(string) >= 65000:
        return jsonify({"error": "Feedback content is empty or exceeds maximum length"}), 400
    
    # DB connection
    mysql = current_app.extensions.get('mysql')
    if not mysql:
        return jsonify({"error": "Database connection not initialized"}), 500

    # Generating feedback UUID
    feedback_uuid = str(uuid.uuid4())
    
    try:
        # Inserting feedback
        cursor = mysql.connect().cursor()
        cursor.execute(
            'INSERT INTO FEEDBACKS (UUID, USER_ID, CONTENT) VALUES (%s, %s, %s)',
            (feedback_uuid, 1, string)
        )
        mysql.connect().commit()
        cursor.close()
    except Exception as e:
        return jsonify({"error": "Failed to insert feedback"}), 500

    return jsonify({"message": "Feedback submitted successfully"}), 201