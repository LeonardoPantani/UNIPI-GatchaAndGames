from flask import Blueprint, render_template, session, jsonify
from app import db

profile_bp = Blueprint('profile', __name__, template_folder='templates')

@profile_bp.route('/profile', methods=['GET'])
def profile():
    if session.get('username') == None:
        return jsonify({"message": "You must be logged in to access this page."}), 405
    else:
        username = session.get('username')  # Prende il nome utente dalla sessione
        return render_template('profile/profile.html', username=username)