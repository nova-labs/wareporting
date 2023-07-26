from flask import Blueprint, session, redirect, url_for, render_template
from requests_oauthlib import OAuth2Session
from functools import wraps
from datetime import datetime
import requests
import logging
import auth
import wadata
import json

logger = logging.getLogger(__name__)

reports_blueprint = Blueprint('reports', __name__)

# All routes in this blueprint require an active login
@reports_blueprint.before_request
def require_login():
    if 'user_token' not in session:
        logger.debug(f"User token not found in session, redirecting to login.")
        return redirect(url_for('auth.login'))
    
    # confirm that they have the right signoff    
    if 'report_access' not in session:
        logger.debug(f"User report access not determined, checking.")
        try:
            session['report_access'] = auth.check_report_access()
        except Exception as e:
            logger.error(f"Error checking report access: {e}")
            return f"""Error checking report access. Please try again. 
                    Error message was: {e}"""

    if 'report_access' not in session or session['report_access'] != True:
        logger.debug(f"User does not have report access, denied.")
        return "You do not have access to reports. Please contact the administrator."
    logger.debug(f"User report access checked, got {session['report_access']}")

@reports_blueprint.route("/")
def index():
    return f"<p>Report list</p><p><a href='{url_for('reports.test_report')}'>Test report</a></p>"

@reports_blueprint.route("/test_report")
def test_report():    
    filter_string = "StartDate gt 2023-06-25 AND IsUpcoming eq false AND (substringof('Name', '_S') OR substringof('Name', '_P'))"
    json_data = wadata.call_api("Events", filter_string)
     
    cancel_list = ['cancelled', 'canceled', 'cancellled', 'cancselled', 'canelled', 'cancel']
    events = [[event['Id'], event['Name'], event['StartDate']] for event in json_data['Events'] if 
                (not any(word in event['Name'].lower() for word in cancel_list))]
    logger.debug(f"Found {len(events)} events to check.")

    if(len(events) > 250):
        return f"Too many events found: ({len(events)}). Please narrow your search."
    
    logger.debug(f"Events JSON data: {json.dumps(json_data, indent=4)}")

    '''
    We need to find events with instructors that are not checked in.
    '''
    flawed_events = []
    for event in events:        
        json_data = wadata.call_api("EventRegistrations", event_id=event[0])
        
        # RegistrationTypeId does not work, not all instructor registrations use the same id number! grr
        missing_instructors = [entry['DisplayName'] for entry in json_data if 'Instructor' in entry['RegistrationType']['Name'] and entry['IsCheckedIn'] == False]
        if len(missing_instructors) > 0:
            # add the name(s) of the instructor to the event
            event.append(missing_instructors)
            flawed_events.append(event)
        logger.debug(f"Event registration JSON data: {json.dumps(json_data, indent=4)}")

    logger.debug(f"Found {len(flawed_events)} flawed events")

    return render_template("test_report.jinja", event_info=flawed_events)
    
