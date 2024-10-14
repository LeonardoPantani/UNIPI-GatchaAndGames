import os
from flask import Flask
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

# Prepara MYSQL
db = MySQL(app)


# Blueprint registration
from blueprints.auth import auth_bp
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True)