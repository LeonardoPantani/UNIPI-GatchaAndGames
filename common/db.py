import mysql.connector
from flask import current_app, g


def get_db():
    """Warning: this function must be called where app context is available."""
    if "db" not in g:
        db_config = current_app.config["db_config"]
        g.db = mysql.connector.connect(**db_config)
    return g.db
