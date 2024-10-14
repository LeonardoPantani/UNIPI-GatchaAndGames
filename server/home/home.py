from flask import Blueprint, request, jsonify
from app import db

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET'])
def homepage():
    return jsonify({"message": "Ciao!"}), 200