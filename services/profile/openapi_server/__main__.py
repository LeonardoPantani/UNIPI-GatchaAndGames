#!/usr/bin/env python3

import connexion
import os

from openapi_server import encoder

from flask import g
from werkzeug.middleware.proxy_fix import ProxyFix


def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    app = connexion_app.app
    app.json_encoder = encoder.JSONEncoder
    app.wsgi_app = ProxyFix(connexion_app.app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # secret key flask
    app.secret_key = os.environ.get('FLASK_SECRET_KEY')

    # Store DB configuration in app.config
    app.config['DB_CONFIG'] = {
        'host': os.environ.get('MYSQL_HOST'),
        'user': os.environ.get('MYSQL_USER'),
        'password': os.environ.get('MYSQL_PASSWORD'),
        'database': os.environ.get('MYSQL_DB'),
        'port': os.environ.get('MYSQL_PORT'),
        'ssl_ca': '/usr/src/app/ssl/database-ca-cert.pem',
        'ssl_cert': '/usr/src/app/ssl/profile-cert.pem',
        'ssl_key': '/usr/src/app/ssl/profile-key.pem'
    }

    # Close the DB connection after each request
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    # Adding api
    connexion_app.add_api('openapi.yaml',
        arguments={'title': 'Gacha System - OpenAPI 3.0'},
        pythonic_params=True
    )

    # starting flask
    connexion_app.run(
        host='0.0.0.0',
        port=443,
        debug=True,
        ssl_context=(
            '/usr/src/app/ssl/profile-cert.pem',
            '/usr/src/app/ssl/profile-key.pem'
        )
    )


if __name__ == '__main__':
    main()
