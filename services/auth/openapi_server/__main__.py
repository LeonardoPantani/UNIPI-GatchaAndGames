#!/usr/bin/env python3

import connexion
import os
import time

from openapi_server import encoder

from flask import current_app


def main():
    connexion_app = connexion.App(__name__, specification_dir='./openapi/')
    connexion_app.app.json_encoder = encoder.JSONEncoder

    # secret key flask
    connexion_app.app.secret_key = os.environ.get('FLASK_SECRET_KEY')
    
    # Adding api
    connexion_app.add_api('openapi.yaml',
        arguments={'title': 'Gacha System - OpenAPI 3.0'},
        pythonic_params=True
    )

    # Starting Connexion Flask app
    connexion_app.run(host='0.0.0.0', port=8080, debug=True)


if __name__ == '__main__':
    main()
