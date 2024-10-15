from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

auth_bp = Blueprint('auth', __name__, template_folder='templates')

import re
def emailCheck(email):
    if(re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', email)):
        return True
    else:
        return False

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    repeat_password = data.get('repeat_password')

    if not username or not email or not password or not repeat_password:
        flash("All fields are mandatory.", "error")
        return redirect(url_for('auth.register_page'))
    
    if not emailCheck(email):
        flash("The email is invalid.", "error")
        return redirect(url_for('auth.register_page'))
    
    if password != repeat_password:
        flash("The two passwords are not equal.", "error")
        return redirect(url_for('auth.register_page'))
    
    cursor = db.connection.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, generate_password_hash(password)))
    db.connection.commit()
    cursor.close()

    # Se tutto è corretto, crea la sessione
    session['username'] = username
    flash("Register successful.", "success")
    return redirect(url_for('home.homepage'))

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        flash("All fields are mandatory.", "error")
        return redirect(url_for('auth.login_page'))

    cursor = db.connection.cursor()
    cursor.execute("SELECT username, password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        flash("That username was not found.", "error")
        return redirect(url_for('auth.login_page'))

    stored_username, stored_password_hash = user

    if not check_password_hash(stored_password_hash, password):
        flash("The password you entered is incorrect.", "error")
        return redirect(url_for('auth.login_page'))

    # Se tutto è corretto, crea la sessione
    session['username'] = stored_username
    flash("Login successful.", "success")
    return redirect(url_for('home.homepage'))


@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    flash("Logout successful.", "success")
    return redirect(url_for('home.homepage'))

@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "L'email è obbligatoria"}), 400
    
    if not emailCheck(email):
        return jsonify({"error": "L'email fornita non è valida."}), 400

    # Reset password qui
    return jsonify({"message": "Istruzioni per il recupero della password inviate"}), 200