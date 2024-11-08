#!/usr/bin/env python3

import connexion
import os
from openapi_server import encoder
from flask_mysqldb import MySQL

def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    connexion_app.app.json_encoder = encoder.JSONEncoder
    
    # Database configuration
    connexion_app.app.config.update({
        'MYSQL_HOST': os.environ.get('MYSQL_HOST', 'db'),
        'MYSQL_USER': os.environ.get('MYSQL_USER', 'gacha_test_user'),
        'MYSQL_PASSWORD': os.environ.get('MYSQL_PASSWORD', 'gacha_test_password'),
        'MYSQL_DB': os.environ.get('MYSQL_DB', 'gacha_test_db')
    })

    # Initialize MySQL
    mysql = MySQL(connexion_app.app)
    connexion_app.app.extensions['mysql'] = mysql  # Store in extensions instead of config

    connexion_app.add_api('openapi.yaml',
                arguments={'title': 'Gacha System - OpenAPI 3.0'},
                pythonic_params=True)

    connexion_app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    main()