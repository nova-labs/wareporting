import auth
import logging
from time import sleep
import json

logger = logging.getLogger(__name__)

# Wild Apricot is moving to mandatory pagination for list endpoints.  The
# exact size of each page depends on the endpoint but the documentation
# suggests a maximum of 500 records per call.  Use that as a reasonable
# default until a caller specifies otherwise.
PAGE_SIZE = 500


def call_api(
    category,
    filter_string=None,
    select_string=None,
    event_id=None,
    asynchronous=False,
):
    """Call a Wild Apricot API endpoint and automatically page through results."""

    oauth_session = auth.get_oauth_session()
    base_url = f"{auth.WA_API_PREFIX}/{category}"

    base_params = []

    if not asynchronous:
        base_params.append(("$async", "false"))
    if filter_string:
        base_params.append(("$filter", filter_string))
    if select_string:
        base_params.append(("$select", select_string))
    if event_id:
        base_params.append(("eventId", str(event_id)))

    logger.debug(f"API url will be: {base_url}")
    logger.debug(f"API parameters will be: {base_params}")

    # Pagination loop.  Many WA endpoints return a dictionary containing a
    # list of objects under some key (e.g. 'Events', 'Contacts').  Others return
    # a list directly.  We'll accumulate whichever list we encounter and stop
    # once a page returns fewer than PAGE_SIZE records.
    skip = 0
    accumulated = []
    list_key = None

    while True:
        params = list(base_params)
        params.append(("$top", str(PAGE_SIZE)))
        params.append(("$skip", str(skip)))

        request = oauth_session.get(url=base_url, params=params)

        if request.status_code != 200:
            if request.status_code == 401:
                logger.debug(
                    "API call failed with 401, refreshing token and trying again"
                )
                auth.refresh_token()
                oauth_session = auth.get_oauth_session()
                request = oauth_session.get(url=base_url, params=params)
            elif request.status_code == 429:
                logger.debug(
                    "API call failed with 429, sleeping for 10 seconds and trying again"
                )
                sleep(10)
                request = oauth_session.get(url=base_url, params=params)
            else:
                raise Exception(
                    f"API call failed with {request.status_code} {request.text}"
                )

        if request.status_code != 200:
            raise Exception(
                f"Repeated API call failed with {request.status_code} {request.text}"
            )

        data = request.json()

        if list_key is None and isinstance(data, dict):
            # Find the first list in the dictionary; assume that's the payload
            for key, value in data.items():
                if isinstance(value, list):
                    list_key = key
                    break
                if list_key is None:
                    # No list found; return the original response without pagination
                    logger.debug(
                        "Response contained no list; returning raw JSON without pagination"
                    )
                    return data

        if list_key is not None and isinstance(data, dict):
            page_items = data.get(list_key, [])
        else:
            page_items = data if isinstance(data, list) else []

        accumulated.extend(page_items)

        logger.debug(f"Retrieved {len(page_items)} records (skip={skip}).")

        if len(page_items) < PAGE_SIZE:
            # Last page reached
            break
        skip += PAGE_SIZE

    logger.debug("API call successful, returning data.")
    logger.debug("*************************************")
    logger.debug(f"{json.dumps(accumulated, indent=4)}")

    if list_key is not None:
        # Maintain original structure if the response was a dict
        return {list_key: accumulated}
    return accumulated
