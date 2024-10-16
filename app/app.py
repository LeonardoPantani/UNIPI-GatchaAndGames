import os, re, MySQLdb
from flask import Flask, session
from dotenv import dotenv_values
from flask_mysqldb import MySQL

# Inizializza Flask
app = Flask(__name__)

# Carico le variabili da .env
config = dotenv_values(".env")

app.config["MYSQL_HOST"] = config["MYSQL_HOST"]
app.config["MYSQL_USER"] = config["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = config["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = config["MYSQL_DB"]
app.secret_key = config["FLASK_SECRET_KEY"]

# Preparo MYSQL
db = MySQL(app)

# Controllo la connessione al database
try:
    conn = MySQLdb.connect(
        host=config["MYSQL_HOST"],
        user=config["MYSQL_USER"],
        password=config["MYSQL_PASSWORD"],
        db=config["MYSQL_DB"]
    )
    conn.close()
except MySQLdb.OperationalError as e:
    print(f"[!] Errore di connessione al database: {e}")
    quit()

# Registrazione blueprints
from auth.auth import auth_bp
from home.home import home_bp
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

if __name__ == '__main__':
    app.run(debug=True)