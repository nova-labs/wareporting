from flask import Blueprint, session, redirect, url_for, render_template
from requests_oauthlib import OAuth2Session
from functools import wraps
import requests
import logging
import auth

logger = logging.getLogger(__name__)

reports_blueprint = Blueprint('reports', __name__)

# All routes in this blueprint require an active login
@reports_blueprint.before_request
def require_login():
    if 'user_token' not in session:
        logger.debug(f"User token not found in session, redirecting to login.")
        return redirect(url_for('auth.login'))
    if 'api_token' not in session:
        logger.debug(f"API token not found in session, redirecting to login.")
        return redirect(url_for('auth.login'))
    
    # confirm that they have the right signoff    
    if 'report_access' not in session:
        logger.debug(f"User report access not determined, checking.")
        try:
            session['report_access'] = auth.check_report_access()
        except Exception as e:
            logger.error(f"Error checking report access: {e}")
            return f"Error checking report access. Please contact the administrator. {e}"

    if 'report_access' not in session or session['report_access'] != True:
        logger.debug(f"User does not have report access, denied.")
        return "You do not have access to reports. Please contact the administrator."
    logger.debug(f"User report access checked, got {session['report_access']}")

@reports_blueprint.route("/")
def index():
    return "<p>Report list</p>"

@reports_blueprint.route("/test_report")
def report():
    # Use the token to get some data from Wild Apricot
    # ...
    return "<p>Report</p>"
