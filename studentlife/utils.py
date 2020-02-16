import requests
from datetime import datetime, timedelta
import json


def get_new_start_end():
    dates = []
    for event in pull_3year():
        if "Term ends" in event["name"]:
            dates.append(datetime.strptime(event["end"], "%Y-%m-%d").date())
        elif "First Day of Classes" in event["name"]:
            dates.append(datetime.strptime(event["end"], "%Y-%m-%d").date())
    return dates[0], dates[1]

def pull_3year():
    """Returns a list (in JSON format) containing all the events from the Penn iCal Calendar.
    List contains events in chronological order.
    Each element of the list is a dictionary, containing:
        - Name of the event 'name'
        - Start date 'start'
        - End date 'end'
    """
    BASE_URL = "https://www.stanza.co/api/schedules/almanacacademiccalendar/"
    events = []
    for term in ["fall", "summer", "spring"]:
        url = "{}{}{}term.ics".format(BASE_URL, datetime.now().year, term)
        resp = requests.get(url)
        resp.raise_for_status()
        r = resp.text
        lines = r.split("\n")
        d = {}
        for line in lines:
            if line == "BEGIN:VEVENT":
                d = {}
            elif line.startswith("DTSTART"):
                raw_date = line.split(":")[1]
                start_date = datetime.strptime(raw_date, '%Y%m%d').date()
                d['start'] = start_date.strftime('%Y-%m-%d')
            elif line.startswith("DTEND"):
                raw_date = line.split(":")[1]
                end_date = datetime.strptime(raw_date, '%Y%m%d').date()
                d['end'] = end_date.strftime('%Y-%m-%d')
            elif line.startswith("SUMMARY"):
                name = line.split(":")[1]
                d['name'] = str(name).strip()
            elif line == "END:VEVENT":
                events.append(d)

    events.sort(key=lambda d: d['start'])
    return events

if __name__ == "__main__":
    get_new_end()