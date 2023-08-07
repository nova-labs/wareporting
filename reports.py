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
# UNLESS we are connecting on localhost, in dev mode, and 
# WA_REPORTING_DOMAIN is set to localhost
@reports_blueprint.before_request
def require_login():
    if current_app.config["ALLOW_LOCALHOST"] == True and auth.WA_REPORTING_DOMAIN == "localhost" and request.remote_addr == '127.0.0.1':
        session["allow_localhost"] = True
        return

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

# Reports can be slow, so we need to process them asynchronously.
#
# This function starts processor_function as a background task and 
# registers the task id with Flask.
#
def start_report_task(processor_function, *args, **kwargs):
    global executor 

    # Start a long task
    if executor is None:
        executor = Executor(current_app._get_current_object())
    task_id = random.randint(100000, 999999)
    future = executor.submit_stored(task_id, processor_function, *args, **kwargs)

    # Store the Future instance's unique identifier in the user's session
    session["task_id"] = task_id

    # allow time for executor to be registered
    time.sleep(2)

    return

# Reports can be slow, so we need to process them asynchronously.
# 
# This function looks for a currently running process
# with this task id, and returns either a "still processing"
# page, an error page, or the completed future.
#
def get_results_by_task_id(done):
    status_page = None
    future = None

    if "task_id" not in session:
        status_page = f"No job started, do not access this page directly."
        
    if executor is None:        
        status_page = render_template('report/await_processing.jinja', done=done)

    # Find the correct Future instance
    task_id = session["task_id"]

    if not executor.futures.done(task_id):
        logger.debug("Job is still running...")
        status_page = render_template('report/await_processing.jinja', done=done)
    
    if status_page is None:
        # we have finished!
        future = executor.futures.pop(task_id)
        session["task_id"] = None
        if future is None:        
            status_page = f"Future with task_id {task_id} not found"
        else:
            # was there an exception from the future?
            exception = future.exception()
            if exception is not None:
                # The function raised an exception           
                status_page = f"Error running job: {exception}"

    return status_page, future

@reports_blueprint.route("/missing_instructor_checkins")
def report_missing_instructor_checkins():      
    # set reporting start date based on delta_days, defaults to 31 days ago
    try:
        delta_days = int(request.args.get('delta_days', 31))
    except ValueError:
        return f"delta_days value {delta_days} was not an integer."    
    logger.info(f"Looking for missing instructor checkins over the past {delta_days} days.")
    start_date = (datetime.today() - timedelta(days=delta_days)).strftime('%Y-%m-%d')

    start_report_task(get_missing_instructor_checkins, start_date)

    return redirect(url_for('reports.missing_instructor_checkins_complete', done='reports.missing_instructor_checkins_complete'))

def get_missing_instructor_checkins(start_date):  
    filter_string = f"StartDate gt {start_date} AND IsUpcoming eq false AND (substringof('Name', '_S') OR substringof('Name', '_P'))"
    json_data = wadata.call_api("Events", filter_string)
     
    cancel_list = ['cancelled', 'canceled', 'cancellled', 'cancselled', 'canelled', 'cancel']
    events = [[event['Id'], event['Name'], event['StartDate']] for event in json_data['Events'] if 
                (not any(word in event['Name'].lower() for word in cancel_list))]
    logger.info(f"Found {len(events)} events to check.")

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
            event.extend(missing_instructors)
            # and let's reformat the date while we're at it
            try:
                if event[2] != None:
                    event[2] = datetime.strptime(event[2], "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %I%p")
            except Exception as e:
                logger.warning(f"Unable to format date string {event[2]} {e}")
                pass

            flawed_events.append(event)
        logger.debug(f"Event registration JSON data: {json.dumps(json_data, indent=4)}")

    logger.info(f"Found {len(flawed_events)} flawed events")

    return flawed_events, start_date

@reports_blueprint.route("/missing_instructor_checkins_complete")
def missing_instructor_checkins_complete():
    status_page, future = get_results_by_task_id(done='reports.missing_instructor_checkins_complete')

    if status_page is not None:
        return status_page
    else:
        flawed_events, start_date = future.result()            

    return render_template("report/missing_instructor_checkins.jinja", event_info=flawed_events, start_date=start_date, datetime=datetime)

@reports_blueprint.route("/missing_reminder_emails")
def report_missing_reminder_emails():  
    # set reporting end date based on delta_days, defaults to 10 days ahead
    try:
        delta_days = int(request.args.get('delta_days', 10))
    except ValueError:
        return f"delta_days value {delta_days} was not an integer."    
    logger.info(f"Looking for missing reminder e-mails over the past {delta_days} days.")
    end_date = (datetime.today() + timedelta(days=delta_days)).strftime('%Y-%m-%d')

    start_report_task(get_missing_reminder_emails, end_date)

    # return redirect(url_for('reports.missing_reminder_emails_complete', done='reports.missing_reminder_emails_complete'))
    return f"Not implemented yet."

def get_missing_reminder_emails(end_date):
    filter_string = f"EndDate lt {end_date} AND IsUpcoming eq true"
    json_data = wadata.call_api("Events", filter_string)
     
    cancel_list = ['cancelled', 'canceled', 'cancellled', 'cancselled', 'canelled', 'cancel']
    events = [[event['Id'], event['Name'], event['StartDate']] for event in json_data['Events'] if 
                (not any(word in event['Name'].lower() for word in cancel_list))]
    logger.info(f"Found {len(events)} events to check.")

    if(len(events) > 250):
        return f"Too many events found: ({len(events)}). Please narrow your search."
    
    logger.debug(f"Events JSON data: {json.dumps(json_data, indent=4)}")

    '''
    We need to find events where reminder emails have not been set up.
    '''
    flawed_events = []
    
    # TODO: may not be possible with current Wild Apricot API!

    logger.info(f"Found {len(flawed_events)} flawed events")

    return flawed_events, end_date    

@reports_blueprint.route("/missing_reminder_emails_complete")
def missing_reminder_emails_complete():
    status_page, future = get_results_by_task_id(done='reports.missing_reminder_emails_complete')

    if status_page is not None:
        return status_page
    else:
        flawed_events, start_date = future.result()            

    # return render_template("report/missing_reminder_emails.jinja", event_info=flawed_events, end_date=end_date, datetime=datetime)
    return f"Not implemented yet."
