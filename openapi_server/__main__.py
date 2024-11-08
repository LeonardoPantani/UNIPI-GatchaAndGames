#!/usr/bin/env python3

import connexion

from openapi_server import encoder
from dotenv import find_dotenv, dotenv_values
from flask_mysqldb import MySQL
import MySQLdb



def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    connexion_app.app.json_encoder = encoder.JSONEncoder
    connexion_app.add_api('openapi.yaml',
                arguments={'title': 'Gacha System - OpenAPI 3.0'},
                pythonic_params=True)
    
    # Carico le variabili da .env
    config = dotenv_values(find_dotenv())
    print(config)

    connexion_app.app.config["MYSQL_HOST"] = config["MYSQL_HOST"]
    connexion_app.app.config["MYSQL_USER"] = config["MYSQL_USER"]
    connexion_app.app.config["MYSQL_PASSWORD"] = config["MYSQL_PASSWORD"]
    connexion_app.app.config["MYSQL_DB"] = config["MYSQL_DB"]
    connexion_app.app.secret_key = config["FLASK_SECRET_KEY"]
    
    # Preparo MYSQL
    db = MySQL(connexion_app.app)

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

    connexion_app.run(port=8080, debug=True)


if __name__ == '__main__':
    main()
