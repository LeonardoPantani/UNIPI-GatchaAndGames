from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, app
from utils import email_check, username_check
import MySQLdb

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    if not data:
        data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    repeat_password = data.get('repeat_password')
    
    if not username or not email or not password or not repeat_password:
        if request.form: # se la post è dal sito
            flash("All fields are mandatory.", "error")
            return redirect(url_for('auth.register_page'))
        else: # se è una richiesta grezza
            return jsonify({"message": "All fields are mandatory."}), 400
    
    # check email
    if not email_check(email):
        if request.form:
            flash("The email is invalid.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "The email is invalid."}), 400
    
    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            if request.form:
                flash("That email is already in use.", "error")
                return redirect(url_for('auth.register_page'))
            else:
                return jsonify({"message": "That email is already in use."}), 409
        
        # check username
        if len(username) < 5:
            if request.form:
                flash("The username must be at least 5 characters long.", "error")
                return redirect(url_for('auth.register_page'))
            else:
                return jsonify({"message": "The username must be at least 5 characters long."}), 400
        
        if not username_check(username):
            if request.form:
                flash("The username can only contain only letters, numbers and underscores.", "error")
                return redirect(url_for('auth.register_page'))
            else:
                return jsonify({"message": "The username can only contain only letters, numbers and underscores."}), 400
        
        # check password
        if password != repeat_password:
            if request.form:
                flash("The two passwords are not equal.", "error")
                return redirect(url_for('auth.register_page'))
            else:
                return jsonify({"message": "The two passwords are not equal."}), 400
        
        # tutto ok, inserisco l'utente
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                    (username, email, generate_password_hash(password)))
        db.connection.commit()
        cursor.close()
        
        # Se è tutto corretto, creo anche la sessione
        if request.form:
            flash("Register successful.", "success")
            return redirect(url_for('home.homepage'))
        else:
            response = jsonify({"message": "Register successful."})
            session_cookie = request.cookies.get(app.config["SESSION_COOKIE_NAME"])
            if session_cookie:
                response.set_cookie(app.config["SESSION_COOKIE_NAME"], session_cookie, httponly=True)
            return response, 200
    except MySQLdb.Error as e:
        if request.form:
            flash("Internal error.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "Internal error."}), 500

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.form
    if not data:
        data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        if request.form: # se la post è dal sito
            flash("All fields are mandatory.", "error")
            return redirect(url_for('auth.login_page'))
        else: # se è una richiesta grezza
            return jsonify({"message": "All fields are mandatory."}), 400

    try:
        cursor = db.connection.cursor()
        cursor.execute("SELECT username, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
    except MySQLdb.Error as e:
        if request.form:
            flash("Internal error.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "Internal error."}), 500

    if user is None:
        if request.form:
            flash("Invalid credentials.", "error")
            return redirect(url_for('auth.login_page'))
        else:
            return jsonify({"message": "Invalid credentials."}), 400

    stored_username, stored_password_hash = user

    if not check_password_hash(stored_password_hash, password):
        if request.form:
            flash("Invalid credentials.", "error")
            return redirect(url_for('auth.login_page'))
        else:
            return jsonify({"message": "Invalid credentials."}), 400

    # Se tutto è corretto, crea la sessione
    session['username'] = stored_username
    if request.form:
        flash("Login successful.", "success")
        return redirect(url_for('home.homepage'))
    else:
        response = jsonify({"message": "Login successful."})
        session_cookie = request.cookies.get(app.config["SESSION_COOKIE_NAME"])
        if session_cookie:
            response.set_cookie(app.config["SESSION_COOKIE_NAME"], session_cookie, httponly=True)
        return response, 200

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    flash("Logout successful.", "success")
    return redirect(url_for('home.homepage'))