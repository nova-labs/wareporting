import auth
import logging
from time import sleep
import json

logger = logging.getLogger(__name__)

# Wild Apricot is moving to mandatory pagination for list endpoints.
# Maximum size is 100.
PAGE_SIZE = 100


def call_api(
    category,
    filter_string=None,
    select_string=None,
    event_id=None,
    asynchronous=False,
):
    """Call a Wild Apricot API endpoint and automatically page through results when filtering."""

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

    def perform_request(params):
        nonlocal oauth_session
        request = oauth_session.get(url=base_url, params=params)
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
        return request

    if not filter_string:
        request = perform_request(base_params)
        if request.status_code != 200:
            raise Exception(
                f"API call failed with {request.status_code} {request.text}"
            )
        data = request.json()
        logger.debug("API call successful (no pagination), returning data.")
        logger.debug("*************************************")
        logger.debug(f"{json.dumps(data, indent=4)}")
        return data

    skip = 0
    accumulated_list = []
    accumulated_object = None
    collection_key = None

    while True:
        params = list(base_params)
        params.append(("$top", str(PAGE_SIZE)))
        params.append(("$skip", str(skip)))

        request = perform_request(params)

        if request.status_code != 200:
            raise Exception(
                f"API call failed with {request.status_code} {request.text}"
            )

        data = request.json()

        # Handle endpoints that return a raw list (e.g., EventRegistrations)
        if isinstance(data, list):
            accumulated_list.extend(data)
            logger.debug(f"Retrieved {len(data)} records (skip={skip}).")
            if len(data) < PAGE_SIZE:
                # Completed pagination for list response
                logger.debug("API call successful, returning accumulated list data.")
                logger.debug("*************************************")
                logger.debug(f"{json.dumps(accumulated_list, indent=4)}")
                return accumulated_list
            skip += PAGE_SIZE
            continue

        # Handle endpoints that return an object containing the collection (e.g., {'Contacts': [...], 'Count': N})
        if isinstance(data, dict):
            if collection_key is None:
                # Detect the collection key on the first page: the first key whose value is a list
                list_keys = [k for k, v in data.items() if isinstance(v, list)]
                if len(list_keys) == 1:
                    collection_key = list_keys[0]
                    accumulated_object = dict(data)
                    accumulated_object[collection_key] = []
                    logger.debug(f"Detected collection key for pagination: {collection_key}")
                else:
                    # Not a paginated collection response; just return the object
                    logger.debug("API call successful (non-collection object), returning data.")
                    logger.debug("*************************************")
                    logger.debug(f"{json.dumps(data, indent=4)}")
                    return data

            page_items = data.get(collection_key, [])
            accumulated_object[collection_key].extend(page_items)
            logger.debug(
                f"Retrieved {len(page_items)} records for '{collection_key}' (skip={skip})."
            )

            if len(page_items) < PAGE_SIZE:
                # Completed pagination for object-with-collection response
                # If a count field exists, align it with accumulated length
                if 'Count' in accumulated_object and isinstance(accumulated_object['Count'], int):
                    accumulated_object['Count'] = len(accumulated_object[collection_key])
                logger.debug("API call successful, returning accumulated object data.")
                logger.debug("*************************************")
                logger.debug(f"{json.dumps(accumulated_object, indent=4)}")
                return accumulated_object

            skip += PAGE_SIZE
            continue

        # Fallback: unknown response type; return as-is
        logger.debug("API call successful (unknown type), returning data.")
        logger.debug("*************************************")
        logger.debug(f"{json.dumps(data, indent=4)}")
        return data

    # We should never reach here because returns happen inside the loop
    # but keep a defensive return in case of logic changes.
    logger.debug("API pagination loop ended unexpectedly; returning best-effort data.")
    if accumulated_object is not None:
        return accumulated_object
    return accumulated_list
