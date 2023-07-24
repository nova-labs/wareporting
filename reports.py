from flask import Blueprint, session, redirect, url_for, render_template
from requests_oauthlib import OAuth2Session
from functools import wraps
import requests
import logging

logger = logging.getLogger(__name__)

reports_blueprint = Blueprint('reports', __name__)

# All routes in this blueprint require an active login
@reports_blueprint.before_request
def require_login():
    if 'user_token' not in session:
        logger.debug(f"User token not found in session, redirecting to login.")
        return redirect(url_for('auth.login'))
    
    # TODO: confirm that they have the right signoff

@reports_blueprint.route("/")
def index():
    return "<p>Report list</p>"

@reports_blueprint.route("/test_report")
def report():
    # Use the token to get some data from Wild Apricot
    # ...
    return "<p>Report</p>"
