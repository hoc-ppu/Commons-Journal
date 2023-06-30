
from datetime import datetime, timedelta
import requests

def get_dates_from_session(session_code: str) -> tuple[datetime, datetime]:

    """Return a tuple of end date of last session and end of this session

    If end date for last session can not be determined use start date
    of this session instead"""

    # session code e.g. '2015-16'

    # Get the dates from API
    url = "https://whatson-api.parliament.uk/calendar/sessions/list.json"
    response = requests.get(url)

    session_json = response.json()

    session_dict: dict[int, dict] = {}

    session_of_interest_id = -1

    for session_obj in session_json:
        session_dict[session_obj["SessionId"]] = session_obj
        if session_obj["CommonsDescription"] == session_code:
            session_of_interest_id = session_obj["SessionId"]

    if session_of_interest_id == -1:
        raise ValueError(
            f"Dates for session, {session_code} could not be found.\nCheck {url}"
        )

    # see if we can find previous session
    previous_session_id = session_of_interest_id - 1
    if previous_session_id in session_dict:
        start_date_str = session_dict[previous_session_id]["EndDate"]
    else:
        start_date_str = session_dict[session_of_interest_id]["StartDate"]

    end_date_str = session_dict[session_of_interest_id]["EndDate"]

    start_date = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
    if previous_session_id in session_dict:
        # remember to add one day to the end of last session date
        start_date = start_date + timedelta(days=1)

    end_date = datetime.strptime(end_date_str[:10], "%Y-%m-%d")

    return start_date, end_date
