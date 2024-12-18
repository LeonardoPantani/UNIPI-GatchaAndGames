import mysql.connector
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_config = current_app.config["DB_CONFIG"]
        g.db = mysql.connector.connect(**db_config)
    return g.db
