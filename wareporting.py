from flask import Flask
from reports import reports_blueprint
from auth import auth_blueprint
import logging
import os

app = Flask(__name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(reports_blueprint, url_prefix='/reports')
app.secret_key = os.environ['WA_REPORTING_FLASK_SECRET_KEY']

if __name__ == "__main__":
    app.debug = True
    logging.basicConfig(level=logging.DEBUG)
    app.run()