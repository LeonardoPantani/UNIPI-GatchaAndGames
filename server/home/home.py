from flask import Blueprint, render_template, session
from app import db

home_bp = Blueprint('home', __name__, template_folder='templates')

@home_bp.route('/', methods=['GET'])
def homepage():
    username = session.get('username')  # Prende il nome utente dalla sessione
    return render_template('home/homepage.html', username=username)