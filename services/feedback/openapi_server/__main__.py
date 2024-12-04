#!/usr/bin/env python3

import os

import connexion
import urllib3
from flask import g
from flask.json.provider import DefaultJSONProvider
from urllib3.exceptions import InsecureRequestWarning
from werkzeug.middleware.proxy_fix import ProxyFix

from openapi_server import encoder

# these config variables can be used everywhere, even without context
CONFIG = {
    "service_type": os.environ.get("SERVICE_TYPE"),
    "circuit_breaker_fails": int(os.environ.get("CIRCUIT_BREAKER_FAILS")),
    "requests_timeout": int(os.environ.get("REQUESTS_TIMEOUT")),
}


# this must be here to avoid a DeprecationWarning
class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        return encoder.JSONEncoder().encode(obj)

    def loads(self, s, **kwargs):
        return super().loads(s, **kwargs)


def main():
    urllib3.disable_warnings(InsecureRequestWarning)
    connexion_app = connexion.App(__name__, specification_dir="./openapi/")
    app = connexion_app.app
    app.json = CustomJSONProvider(app)
    app.wsgi_app = ProxyFix(connexion_app.app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.secret_key = os.environ.get("FLASK_SECRET_KEY")
    app.config["jwt_secret_key"] = os.environ.get("JWT_SECRET_KEY")
    app.config["requests_timeout"] = int(os.environ.get("REQUESTS_TIMEOUT"))
    app.config["database_timeout"] = int(os.environ.get("DATABASE_TIMEOUT"))

    # these certificates must be stored in the ssl folder for the DB connection to work:
    # database-ca-cert.pem
    # <service_type>-cert.pem
    # <service_type>-key.pem
    app.config["db_config"] = {
        "host": os.environ.get("MYSQL_HOST"),
        "user": os.environ.get("MYSQL_USER"),
        "password": os.environ.get("MYSQL_PASSWORD"),
        "database": os.environ.get("MYSQL_DB"),
        "port": os.environ.get("MYSQL_PORT"),
        "ssl_ca": "/usr/src/app/ssl/database-ca-cert.pem",
        "ssl_cert": "/usr/src/app/ssl/" + CONFIG["service_type"] + "-cert.pem",
        "ssl_key": "/usr/src/app/ssl/" + CONFIG["service_type"] + "-key.pem",
    }

    # close db after request
    @app.teardown_appcontext
    def close_db(error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # adding api
    connexion_app.add_api("openapi.yaml", arguments={"title": "Gacha System - OpenAPI 3.0"}, pythonic_params=True)

    # starting flask
    # these certificates must be stored in the ssl folder to activate HTTPS for this service:
    # database-ca-cert.pem
    # <service_type>-cert.pem
    # <service_type>-key.pem
    connexion_app.run(
        host="0.0.0.0",
        port=443,
        debug=True,
        ssl_context=(
            "/usr/src/app/ssl/" + CONFIG["service_type"] + "-cert.pem",
            "/usr/src/app/ssl/" + CONFIG["service_type"] + "-key.pem",
        ),
    )


if __name__ == "__main__":
    main()
