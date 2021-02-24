import os

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from requests.exceptions import HTTPError

from laundry.models import LaundryRoom, LaundrySnapshot


LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
HALL_URL = f"{LAUNDRY_URL}/?location="


def update_machine_object(cols, machine_object):
    """
    Updates Machine status and time remaining
    """

    if cols[2].getText() == "In use" or cols[2].getText() == "Almost done":
        time_remaining = cols[3].getText().split(" ")[0]
        machine_object["running"] += 1
        try:
            machine_object["time_remaining"].append(int(time_remaining))
        except ValueError:
            pass
    elif cols[2].getText() == "Out of order":
        machine_object["out_of_order"] += 1
    elif cols[2].getText() == "Not online":
        machine_object["offline"] += 1
    else:
        machine_object["open"] += 1

    # edge case that handles machine not sending time data
    diff = int(machine_object["running"]) - len(machine_object["time_remaining"])
    while diff > 0:
        machine_object["time_remaining"].append(-1)
        diff = diff - 1

    return machine_object


def parse_a_hall(hall_link):
    """
    Return names, hall numbers, and the washers/dryers available for a certain hall_id
    """

    page = requests.get(hall_link, timeout=60)
    soup = BeautifulSoup(page.content, "html.parser")
    soup.prettify()
    washers = {"open": 0, "running": 0, "out_of_order": 0, "offline": 0, "time_remaining": []}
    dryers = {"open": 0, "running": 0, "out_of_order": 0, "offline": 0, "time_remaining": []}

    detailed = []

    rows = soup.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 1:
            machine_type = cols[1].getText()
            if machine_type == "Washer":
                washers = update_machine_object(cols, washers)
            elif machine_type == "Dryer":
                dryers = update_machine_object(cols, dryers)
            if machine_type in ["Washer", "Dryer"]:
                try:
                    time = int(cols[3].getText().split(" ")[0])
                except ValueError:
                    time = 0
                detailed.append(
                    {
                        "id": int(cols[0].getText().split(" ")[1][1:]),
                        "type": cols[1].getText().lower(),
                        "status": cols[2].getText(),
                        "time_remaining": time,
                    }
                )

    machines = {"washers": washers, "dryers": dryers, "details": detailed}
    return machines


def check_is_working():
    """
    Returns True if the wash alert web interface seems to be working properly, or False otherwise.
    """

    try:
        r = requests.post(
            "{}/".format(LAUNDRY_URL),
            timeout=60,
            data={
                "locationid": "5faec7e9-a4aa-47c2-a514-950c03fac460",
                "email": "pennappslabs@gmail.com",
                "washers": 0,
                "dryers": 0,
                "locationalert": "OK",
            },
        )
        r.raise_for_status()
        return (
            "The transaction log for database 'QuantumCoin' is full due to 'LOG_BACKUP'."
            not in r.text
        )
    except requests.exceptions.HTTPError:
        return False


def all_status():
    """
    Return names, hall numbers, and the washers/dryers available for all rooms in the system
    """

    if not check_is_working():
        raise HTTPError()

    laundry_rooms = {}
    for room in LaundryRoom.objects.all():
        laundry_rooms[room.name] = parse_a_hall(HALL_URL + str(room.uuid))
    return laundry_rooms


def hall_status(hall_id):
    """
    Return the status of each specific washer/dryer in a particular hall_id
    """

    if not check_is_working():
        raise HTTPError()

    try:
        room = LaundryRoom.objects.get(hall_id=hall_id)
    except LaundryRoom.DoesNotExist:
        raise ValueError("No hall with id %s exists." % hall_id)

    machines = parse_a_hall(HALL_URL + str(room.uuid))

    return {"machines": machines, "hall_name": room.name, "location": room.location}


def save_data():
    """
    Retrieves current laundry info and saves it into the database.
    """

    now = timezone.localtime()

    if LaundrySnapshot.objects.filter(date=now).count() == 0:
        data = all_status()

        for name, room in data.items():

            laundry_room = LaundryRoom.objects.get(name=name)

            LaundrySnapshot.objects.create(
                room=laundry_room,
                date=now,
                available_washers=room["washers"]["open"],
                available_dryers=room["dryers"]["open"],
            )
