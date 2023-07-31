from flask import Blueprint, session, redirect, url_for, render_template, request, current_app
from flask_executor import Executor
from requests_oauthlib import OAuth2Session
from functools import wraps
from datetime import datetime, timedelta
import requests
import logging
import auth
import wadata
import json
import random
import time

logger = logging.getLogger(__name__)

reports_blueprint = Blueprint('reports', __name__)
executor = None

# All routes in this blueprint require an active login
@reports_blueprint.before_request
def require_login():
    if 'user_token' not in session:
        logger.info(f"User token not found in session, redirecting to login.")
        return redirect(url_for('auth.login'))
    
    # confirm that they have the right signoff    
    if 'report_access' not in session:
        logger.info(f"User report access not determined, checking.")
        try:
            session['report_access'] = auth.check_report_access()
        except Exception as e:
            logger.error(f"Error checking report access: {e}")
            return f"""Error checking report access. Please try again. 
                    Error message was: {e}"""

    if 'report_access' not in session or session['report_access'] != True:
        logger.info(f"User does not have report access, denied.")
        return "You do not have access to reports. Please contact the administrator."
    logger.info(f"User report access checked, got {session['report_access']}")

@reports_blueprint.route("/")
def index():
    return render_template("catalog.jinja")

@reports_blueprint.route("/missing_instructor_checkins")
def report_missing_instructor_checkins():  
    global executor 

    # set reporting start date based on delta_days, defaults to 31 days ago
    try:
        delta_days = int(request.args.get('delta_days', 31))
    except ValueError:
        return f"delta_days value {delta_days} was not an integer."    
    logger.info(f"Looking for missing instructor checkins over the past {delta_days} days.")
    start_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y-%m-%d')

    # Start a long task
    if executor is None:
        executor = Executor(current_app._get_current_object())
    task_id = random.randint(100000, 999999)
    future = executor.submit_stored(task_id, get_missing_instructor_checkins, start_date)
    # Store the Future instance's unique identifier in the user's session
    session["task_id"] = task_id

    # allow time for executor to be registered
    time.sleep(2)

    return redirect(url_for('reports.missing_instructor_checkins_complete', done='reports.missing_instructor_checkins_complete'))

def get_missing_instructor_checkins(start_date):  
    filter_string = f"StartDate gt {start_date} AND IsUpcoming eq false AND (substringof('Name', '_S') OR substringof('Name', '_P'))"
    json_data = wadata.call_api("Events", filter_string)
     
    cancel_list = ['cancelled', 'canceled', 'cancellled', 'cancselled', 'canelled', 'cancel']
    events = [[event['Id'], event['Name'], event['StartDate']] for event in json_data['Events'] if 
                (not any(word in event['Name'].lower() for word in cancel_list))]
    logger.info(f"Found {len(events)} events to check.")

    # if(len(events) > 250):
    #     return f"Too many events found: ({len(events)}). Please narrow your search."
    
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
            event.extend(missing_instructors)
            # and let's reformat the date while we're at it
            try:
                if event[2] != None:
                    event[2] = datetime.strptime(event[2], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %I%p")
            except Exception as e:
                logger.warn(f"Unable to format date string {event[2]} {e}")
                pass

            flawed_events.append(event)
        logger.debug(f"Event registration JSON data: {json.dumps(json_data, indent=4)}")

    logger.info(f"Found {len(flawed_events)} flawed events")

    return flawed_events, start_date

@reports_blueprint.route("/missing_instructor_checkins_complete")
def missing_instructor_checkins_complete():
    if "task_id" not in session:
        return f"No job started, do not access this page directly."
        
    if executor is None:        
        return render_template('report/await_processing.jinja', done='reports.missing_instructor_checkins_complete')

    # Find the correct Future instance
    task_id = session["task_id"]

    if not executor.futures.done(task_id):
        logger.debug("Job is still running...")
        return render_template('report/await_processing.jinja', done='reports.missing_instructor_checkins_complete')
    
    future = executor.futures.pop(task_id)
    session["task_id"] = None
    if future is None:        
        return f"Future with task_id {task_id} not found"

    # Get the result (or exception) from the Future
    exception = future.exception()
    if exception is not None:
        # The function raised an exception           
        return f"Error running job: {exception}"
    else:
        flawed_events, start_date = future.result()            

    return render_template("report/missing_instructor_checkins.jinja", event_info=flawed_events, start_date=start_date, datetime=datetime)
