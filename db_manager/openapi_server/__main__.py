#!/usr/bin/env python3

import connexion
import os
from flask import g
from openapi_server import encoder


def main():
    connexion_app = connexion.App(__name__, specification_dir="./openapi/")
    flask_app = connexion_app.app
    flask_app.json_encoder = encoder.JSONEncoder

    # Secret key for Flask
    flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY")

    # Store DB configuration in app.config
    flask_app.config["DB_CONFIG"] = {
        "host": os.environ.get("MYSQL_HOST"),
        "user": os.environ.get("MYSQL_USER"),
        "password": os.environ.get("MYSQL_PASSWORD"),
        "database": os.environ.get("MYSQL_DB"),
        "ssl_ca": "/usr/src/app/ssl/ca.pem",
        "ssl_cert": "/usr/src/app/ssl/client-cert.pem",
        "ssl_key": "/usr/src/app/ssl/client-key.pem",
    }

    # Close the DB connection after each request
    @flask_app.teardown_appcontext
    def close_db(error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Adding API
    connexion_app.add_api(
        "openapi.yaml", arguments={"title": "DBManager for Gacha System - OpenAPI 3.0"}, pythonic_params=True
    )

    # Starting Connexion Flask app
    connexion_app.run(host="0.0.0.0", port=8080, debug=True)


if __name__ == "__main__":
    main()
