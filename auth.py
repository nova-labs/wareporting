from flask import Blueprint, session, request, redirect, url_for, render_template
import requests
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import os
import logging
import base64
import json

logger = logging.getLogger(__name__)

auth_blueprint = Blueprint('auth', __name__)

# Wild Apricot credentials, secrets are in environment variables
WA_REPORTING_CLIENT_SECRET = os.environ['WA_REPORTING_CLIENT_SECRET']
WA_REPORTING_API_KEY = os.environ['WA_REPORTING_API_KEY']
WA_API_PREFIX = "https://api.wildapricot.org/v2.2/Accounts/335649"
'''
note that WA_REPORTING_DOMAIN must:
1. Support HTTPS
2. Be listed as a trusted redirect domain in the WA settings for this 
authorized application. Without this, the oauth signin page will just
say "an error occurred" and not give any details.

Use ngrok for local development, but be aware of condition 2 above. Use
your free static domain name.
'''
WA_REPORTING_DOMAIN = os.environ['WA_REPORTING_DOMAIN']

WILD_APRICOT_CLIENT_ID = "jz0nsf5dl4"
WILD_APRICOT_REDIRECT_URI = f"https://{WA_REPORTING_DOMAIN}/callback"

@auth_blueprint.route("/")
def index():
    logged_in = False
    if 'user_token' in session:
        logged_in = True
    return render_template("index.jinja", logged_in=logged_in)

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
                                     client_secret=WA_REPORTING_CLIENT_SECRET,                                     
                                     code=authorization_code,                                     
                                     scope=["contacts_me"])
    
    if token != None:
        logger.debug(f"User token received.")        

        # Store the token in the session
        session['user_token'] = token
        logger.debug(f"User token stored in session.")
        refresh_token()
        return redirect(url_for('reports.index'))
    else:
        logger.warn(f"User token not received. Login error?")
        return "User login token not received. Please try again."

def refresh_token():
    # The URL for API tokens
    api_token_url = "https://oauth.wildapricot.org/auth/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "auto"
    }
    # Send a POST request with Basic Authorization and form data
    response = requests.post(api_token_url, auth=HTTPBasicAuth("APIKEY", WA_REPORTING_API_KEY), data=data)

    # Check if the request was successful
    if response.status_code == 200:
        api_token = response.json().get('access_token')
        # Store the API token in the session
        session['api_token'] = api_token
        logger.debug(f"API token stored in session.")
    else:
        # Handle the error, force user logout
        session.clear()        
        return f"Error getting API token, response code was {response.status_code}. Please try again."

@auth_blueprint.route("/logout")
def logout():
    session.clear()
    return render_template("index.jinja", logged_in=False)

def get_oauth_session():
    if 'api_token' not in session:
        refresh_token()

    # Bearer token
    token = {
        'access_token': session['api_token'], 
        'token_type': 'Bearer'
    }
    oauth_session = OAuth2Session(token=token)
    return oauth_session

def check_report_access():
    # Use the user token to get the current user's info
    oauth_user = OAuth2Session(token=session['user_token'])    
    response = oauth_user.get(url = f"{WA_API_PREFIX}/contacts/me")

    if response.status_code == 200:
        logger.debug(f"Response from Wild Apricot:\n {json.dumps(response.json(), indent=4)}")

        # we got it, now use the contact id to get the contact's fields        
        contact_id = response.json().get('Id')
        oauth_app = get_oauth_session()
        
        logger.debug(f"About to call the API for user's signoffs with contact id {contact_id}...")
        response = oauth_app.get(url = f"{WA_API_PREFIX}/contacts/{contact_id}",
                                 params = {("&async", "false"), ("&includeFieldValues", "true")})
        
        if response.status_code == 200:
            logger.debug(f"Response from Wild Apricot:\n {json.dumps(response.json(), indent=4)}")
            '''
            see https://app.swaggerhub.com/apis-docs/WildApricot/wild-apricot_api_for_non_administrative_access/7.15.0#/Contacts/get_accounts__accountId__contacts_me
            need signoff [NL] wautils (will be [NL] reporting), from field name "NL Signoffs and Categories" 
            see https://github.com/nova-labs/watto/blob/main/app/models/field.rb and
            https://github.com/nova-labs/watto/blob/main/app/models/user.rb
            based on what I see in the portal, if a signoff with the right name exists, the user has it.
            '''
            # Extract the FieldValues list
            field_values = response.json().get('FieldValues', [])

            # Find the NL Signoffs and Categories field
            signoffs_field = next((field for field in field_values if field['FieldName'] == 'NL Signoffs and Categories'), None)
            # If the field was found and it has a non-empty value, check if [NL] reporting is present
            if signoffs_field and signoffs_field['Value']:
                labels = [item['Label'] for item in signoffs_field['Value']]
                if '[NL] reporting' in labels:
                    return True
                else:
                    return False
            else:
                logger.warn("NL Signoffs and Categories field is not present or has an empty value")
                return False

        else:
            raise Exception(f"Error getting user signoffs, response code was {response.status_code}.")
    else:        
        raise Exception(f"Error getting user info, response code was {response.status_code}.")
    return False