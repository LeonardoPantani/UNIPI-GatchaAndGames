import connexion
from typing import Dict
from typing import Tuple
from typing import Union

from openapi_server import util

from flask import jsonify


def health_check():
    return jsonify({"message": "Service operational."}), 200