import auth
import logging
from time import sleep
import json

logger = logging.getLogger(__name__)

def call_api(category, filter_string=None, event_id=None, asynchronous=False):
    oauth_session = auth.get_oauth_session()
    url = f"{auth.WA_API_PREFIX}/{category}"

    params = []

    if not asynchronous:
        params.append(("$async", "false"))
    if filter_string:
        params.append(("$filter", filter_string))
    if event_id:
        params.append(("eventId", str(event_id)))

    logger.debug(f"API url will be: {url}")
    logger.debug(f"API parameters will be: {params}")
    
    request = oauth_session.get(url = url, params = params)    

    if request.status_code != 200:
        if request.status_code == 401:
            logger.debug("API call failed with 401, refreshing token and trying again")
            auth.refresh_token()
            oauth_session = auth.get_oauth_session()
        elif request.status_code == 429:
            logger.debug("API call failed with 429, sleeping for 10 seconds and trying again")
            sleep(10)
        else:
            raise Exception(f"API call failed with {request.status_code} {request.text}")
        
    # did we get it?
    if request.status_code != 200:
        logger.debug("Trying API call again.")
        request = oauth_session.get(url = url, params = params)

    if request.status_code != 200:
        raise Exception(f"Repeated API call failed with {request.status_code} {request.text}")
    
    logger.debug(f"API call successful, returning data.")
    logger.debug("*************************************")
    logger.debug(f"{json.dumps(request.json(), indent=4)}")
    return request.json()
