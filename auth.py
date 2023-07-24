from flask import Blueprint, session, request, redirect, url_for
import requests
from requests_oauthlib import OAuth2Session
from reports import reports_blueprint
import os
import logging
import base64

logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

# Wild Apricot credentials, secrets are in environment variables
WILD_APRICOT_CLIENT_ID = "jz0nsf5dl4"
WILD_APRICOT_CLIENT_SECRET = os.environ['WILD_APRICOT_CLIENT_SECRET']
WILD_APRICOT_API_KEY = os.environ['WILD_APRICOT_API_KEY']
WILD_APRICOT_REDIRECT_URI = "https://better-ram-properly.ngrok-free.app/callback"

@auth_blueprint.route("/")
def index():
    return "<p>Hello, this is the auth index</p>"

@auth_blueprint.route("/login")
def login():
    # Redirect user to Wild Apricot for login
    wild_apricot = OAuth2Session(WILD_APRICOT_CLIENT_ID, 
                                 redirect_uri=WILD_APRICOT_REDIRECT_URI,
                                 scope=["contacts_me"])
    authorization_url, state = wild_apricot.authorization_url("https://novalabs.wildapricot.org/sys/login/OAuthLogin")
    logger.debug(f"Initial login complete, redirecting to {authorization_url}")
    return redirect(authorization_url)

@auth_blueprint.route("/callback")
def callback():
    # User has logged in, now get an access token
    authorization_code = request.args.get('code')    
    if authorization_code == None:
        return "Authorization code not received in callback. Please login again."
    wild_apricot = OAuth2Session(WILD_APRICOT_CLIENT_ID, 
                                 redirect_uri=WILD_APRICOT_REDIRECT_URI)
    token = wild_apricot.fetch_token("https://oauth.wildapricot.org/auth/token", 
                                     client_secret=WILD_APRICOT_CLIENT_SECRET,                                     
                                     code=authorization_code,                                     
                                     scope=["contacts_me"])
    
    if token != None:
        logger.debug(f"User token received.")        

        # Store the token in the session
        session['user_token'] = token
        logger.debug(f"User token stored in session.")
    else:
        logger.warn(f"User token not received. Login error?")

    # The URL for API tokens
    api_token_url = "https://oauth.wildapricot.org/auth/token"

    # Base64 encode the API key
    auth_str = f"APIKEY:{WILD_APRICOT_API_KEY}"
    auth_str_encoded = base64.b64encode(auth_str.encode()).decode()

    # The headers for the request
    headers = {
        "Authorization": f"Basic {auth_str_encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # The data for the request
    data = {
        "grant_type": "client_credentials",
        "scope": "auto"
    }

    # Send a POST request with Basic Authorization and form data
    response = requests.post(api_token_url, headers=headers, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        api_token = response.json().get('access_token')
        # Store the API token in the session
        session['api_token'] = api_token
        logger.debug(f"API token stored in session.")
    else:
        # Handle the error
        session.pop('user_token', None)
        api_token = None
        return f"Error getting API token, response code was {response.status_code}. Please try again."

    return redirect(url_for('reports.index'))