from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from utils import emailCheck
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

    if len(username) < 5:
        if request.form:
            flash("The username is invalid.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "The username is invalid."}), 400

    if not emailCheck(email):
        if request.form:
            flash("The email is invalid.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "The email is invalid."}), 400
    
    if password != repeat_password:
        if request.form:
            flash("The two passwords are not equal.", "error")
            return redirect(url_for('auth.register_page'))
        else:
            return jsonify({"message": "The two passwords are not equal."}), 400
    
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
        
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, generate_password_hash(password)))
        db.connection.commit()
        cursor.close()
        
        if request.form:
            session['username'] = username
            flash("Register successful.", "success")
            return redirect(url_for('home.homepage'))
        else:
            return jsonify({"message": "Register successful."}), 200
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