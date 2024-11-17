import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import HTTPError

from laundry.models import LaundryRoom, LaundrySnapshot


def get_room_url(room_id: int):
    return f"{settings.LAUNDRY_URL}/rooms/{room_id}/machines?raw=true"


def get_validated(url):
    """
    Makes a request to the given URL and returns the JSON response if the request is successful.
    Uses headers specific to the laundry API and should not be used for other requests.
    @param url: The URL to make the request to.
    @return: The JSON response if the request is successful, otherwise None.
    """
    try:
        request = requests.get(url, timeout=60, headers=settings.LAUNDRY_HEADERS)
        request.raise_for_status()
        return request.json()
    except HTTPError as e:
        print(f"Error: {e}")
        return None


def update_machine_object(machine, machine_type_data):
    """
    Updates Machine status and time remaining
    """

    #  TODO: Early stage in update 9/29/2024, known status codes are
    #  TODO: "IN_USE", "AVAILABLE", "COMPLETE";
    #  TODO: need to update if we identify other codes, especially error
    status = machine["currentStatus"]["statusId"]
    if status == "IN_USE":
        time_remaining = machine["currentStatus"]["remainingSeconds"]
        machine_type_data["running"] += 1
        try:
            machine_type_data["time_remaining"].append(int(time_remaining))
        except ValueError:
            pass
    elif status in ["AVAILABLE", "COMPLETE"]:
        machine_type_data["open"] += 1
    # TODO: Verify there are no other statuses
    else:
        machine_type_data["offline"] += 1

    # edge case that handles machine not sending time data
    # TODO: I don't think we need this?
    diff = int(machine_type_data["running"]) - len(machine_type_data["time_remaining"])
    while diff > 0:
        machine_type_data["time_remaining"].append(-1)
        diff = diff - 1

    return machine_type_data


def parse_a_room(room_request_link):
    """
    Return names, hall numbers, and the washers/dryers available for a certain room_id
    """

    washers = {"open": 0, "running": 0, "out_of_order": 0, "offline": 0, "time_remaining": []}
    dryers = {"open": 0, "running": 0, "out_of_order": 0, "offline": 0, "time_remaining": []}

    detailed = []

    request_json = get_validated(room_request_link)
    if request_json is None:
        return {"washers": washers, "dryers": dryers, "details": detailed}

    [
        update_machine_object(machine, washers) if machine["isWasher"] else None
        for machine in request_json
    ]
    [
        update_machine_object(machine, dryers) if machine["isDryer"] else None
        for machine in request_json
    ]
    [
        detailed.append(
            {
                "id": machine["id"],
                "type": "washer" if machine["isWasher"] else "dryer",
                "status": machine["currentStatus"]["statusId"],
                "time_remaining": machine["currentStatus"]["remainingSeconds"],
            }
        )
        for machine in request_json
        if machine["isWasher"] or machine["isDryer"]
    ]

    return {"washers": washers, "dryers": dryers, "details": detailed}


def check_is_working():
    """
    Returns True if the wash alert web interface seems to be working properly, or False otherwise.
    """

    all_rooms_request = get_validated(f"{settings.LAUNDRY_URL}/geoBoundaries/5610?raw=true")
    if all_rooms_request is None:
        return False
    return True


def all_status():
    """
    Return names, hall numbers, and the washers/dryers available for all rooms in the system
    """

    return {
        room.name: parse_a_room(get_room_url(room.room_id)) for room in LaundryRoom.objects.all()
    }


def room_status(room):
    """
    Return the status of each specific washer/dryer in a particular hall_id
    """

    machines = parse_a_room(get_room_url(room.room_id))

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
