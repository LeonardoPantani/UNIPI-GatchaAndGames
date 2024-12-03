#!/usr/bin/env python3

import os

import connexion
import urllib3
from flask.json.provider import DefaultJSONProvider
from urllib3.exceptions import InsecureRequestWarning
from werkzeug.middleware.proxy_fix import ProxyFix

from openapi_server import encoder


class CustomJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        return encoder.JSONEncoder().encode(obj)

    def loads(self, s, **kwargs):
        return super().loads(s, **kwargs)


def main():
    urllib3.disable_warnings(InsecureRequestWarning)
    connexion_app = connexion.App(__name__, specification_dir="./openapi/")
    flask_app = connexion_app.app
    flask_app.json = CustomJSONProvider(flask_app)
    flask_app.wsgi_app = ProxyFix(connexion_app.app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    flask_app.secret_key = os.environ.get("FLASK_SECRET_KEY")
    flask_app.config["jwt_secret_key"] = os.environ.get("JWT_SECRET_KEY")
    flask_app.config["circuit_breaker_fails"] = int(os.environ.get("CIRCUIT_BREAKER_FAILS"))
    flask_app.config["requests_timeout"] = int(os.environ.get("REQUESTS_TIMEOUT"))
    flask_app.config["database_timeout"] = int(os.environ.get("DATABASE_TIMEOUT"))

    # adding api
    connexion_app.add_api("openapi.yaml", arguments={"title": "Gacha System - OpenAPI 3.0"}, pythonic_params=True)

    # starting flask
    connexion_app.run(
        host="0.0.0.0",
        port=443,
        debug=True,
        ssl_context=("/usr/src/app/ssl/admin-cert.pem", "/usr/src/app/ssl/admin-key.pem"),
    )


if __name__ == "__main__":
    main()
