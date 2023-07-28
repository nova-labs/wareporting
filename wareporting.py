from dotenv import load_dotenv
# If a .env file is found it will override the environment!
# Should be used only for development, and not added to git
# (there is a .gitignore directive already)
load_dotenv() 

from flask import Flask
from reports import reports_blueprint
from auth import auth_blueprint
import logging
import os

# This code sets up the flask application and registers the auth and reports
# blueprints. It also sets a secret key which is used to sign session cookies
# and other things. The secret key is stored in the environment variable
# WA_REPORTING_FLASK_SECRET_KEY
app = Flask(__name__)
app.register_blueprint(auth_blueprint)
app.register_blueprint(reports_blueprint, url_prefix='/reports')
app.secret_key = os.environ['WA_REPORTING_FLASK_SECRET_KEY']

if __name__ == "__main__":
    # This code will only run if you run this file directly. It will not run
    # for production servers. It sets up useful logging.
    app.debug = True
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('reports').setLevel(logging.DEBUG)
    logging.getLogger('wareporting').setLevel(logging.DEBUG)
    #logging.getLogger('wadata').setLevel(logging.DEBUG)

    app.run()