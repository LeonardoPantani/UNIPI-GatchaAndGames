#!/usr/bin/env python3

import connexion
import os
import time

from openapi_server import encoder

from flaskext.mysql import MySQL
from flask import current_app


def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    connexion_app.app.json_encoder = encoder.JSONEncoder

    # Initialize MySQL
    mysql = MySQL()
    
    # Flask app configuration (db values + secret key)
    connexion_app.app.config["MYSQL_DATABASE_USER"] = os.environ.get('MYSQL_USER')
    connexion_app.app.config["MYSQL_DATABASE_PASSWORD"] = os.environ.get('MYSQL_PASSWORD')
    connexion_app.app.config["MYSQL_DATABASE_DB"] = os.environ.get('MYSQL_DB')
    connexion_app.app.config["MYSQL_DATABASE_HOST"] = os.environ.get('MYSQL_HOST')
    connexion_app.app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    
    mysql.init_app(connexion_app.app)

    # Tentativi per connettersi al database
    for attempt in range(1, 21):
        try:
            # Prova a ottenere il cursore
            connection = mysql.connect()
            cursor = connection.cursor()
            cursor.close()
            break
        except Exception as e:
            print(f"Attempt {attempt}: error while connecting to db: {e}")
            if attempt == 20:
                print("Unable to connect. Not retrying anymore.")
                return
            time.sleep(1)

    connexion_app.app.extensions['mysql'] = mysql
    
    # Adding api
    connexion_app.add_api('openapi.yaml',
        arguments={'title': 'Gacha System - OpenAPI 3.0'},
        pythonic_params=True
    )

    # Starting Connexion Flask app
    connexion_app.run(host='0.0.0.0', port=3005, debug=True)


if __name__ == '__main__':
    main()
