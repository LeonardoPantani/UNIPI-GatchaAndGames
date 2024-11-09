#!/usr/bin/env python3

import connexion
import os
import MySQLdb
from openapi_server import encoder
from flask_mysqldb import MySQL

def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    connexion_app.app.json_encoder = encoder.JSONEncoder
    
    # Flask app configuration (db values + secret key)
    connexion_app.app.config.update({
        'MYSQL_HOST': os.environ.get('MYSQL_HOST'),
        'MYSQL_USER': os.environ.get('MYSQL_USER'),
        'MYSQL_PASSWORD': os.environ.get('MYSQL_PASSWORD'),
        'MYSQL_DB': os.environ.get('MYSQL_DB')
    })
    connexion_app.app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    # Initialize MySQL
    mysql = MySQL(connexion_app.app)
    connexion_app.app.extensions['mysql'] = mysql  # Store in extensions instead of config

    # Check database connection
    # try:
    #     conn = MySQLdb.connect(
    #         host=os.environ.get('MYSQL_HOST'),
    #         user=os.environ.get('MYSQL_USER'),
    #         password=os.environ.get('MYSQL_PASSWORD'),
    #         db=os.environ.get('MYSQL_DB')
    #     )
    #     conn.close()
    # except MySQLdb.OperationalError as e:
    #     print(f"[!] Errore di connessione al database: {e}")
        

    
    # Adding api
    connexion_app.add_api('openapi.yaml',
                arguments={'title': 'Gacha System - OpenAPI 3.0'},
                pythonic_params=True)


    # Starting Connexion Flask app
    connexion_app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == '__main__':
    main()