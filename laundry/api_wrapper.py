import os

import requests
from bs4 import BeautifulSoup
from django.core.management import call_command
from django.db.utils import OperationalError
from django.utils import timezone

from laundry.models import LaundryRoom, LaundrySnapshot


LAUNDRY_URL = os.environ.get("LAUNDRY_URL", "http://suds.kite.upenn.edu")
ALL_URL = f"{LAUNDRY_URL}/?location="

# USAGE_BASE_URL from LAS does not work


class Laundry(object):
    def __init__(self):
        self.busy_dict = {
            "LowBusyNightColor": "Low",
            "LowBusyDayColor": "Low",
            "MediumLowBusyColor": "Medium",
            "MediumHighBusyColor": "High",
            "HighBusyColor": "Very High",
            "NoDataBusyColor": "No Data",
        }
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.hall_to_link = {}
        self.id_to_hall = {}
        self.id_to_location = {}
        self.hall_id_list = []
        self.create_hall_to_link_mapping()

    def create_hall_to_link_mapping(self):
        try:
            # makes migration when there are no rooms
            if LaundryRoom.objects.count() == 0:
                call_command("uuid_migration")

            for room in LaundryRoom.objects.all():
                hall_id = room.hall_id
                self.hall_to_link[room.name] = ALL_URL + str(room.uuid)
                self.id_to_hall[hall_id] = room.name
                self.id_to_location[hall_id] = room.location
                self.hall_id_list.append(
                    {"hall_name": room.name, "id": room.hall_id, "location": room.location}
                )
        # OperationalError thrown when initially making migrations
        except OperationalError:
            return

    @staticmethod
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

    def parse_a_hall(self, hall):
        """Return names, hall numbers, and the washers/dryers available for a certain hall.
        :param hall:
            The ID of the hall to retrieve data for.
        :type hall: int
        """
        if hall not in self.hall_to_link:
            return None  # change to to empty json idk
        page = requests.get(self.hall_to_link[hall], timeout=60)
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
                    washers = Laundry.update_machine_object(cols, washers)
                elif machine_type == "Dryer":
                    dryers = Laundry.update_machine_object(cols, dryers)
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

    def all_status(self):
        """Return names, hall numbers, and the washers/dryers available for all
        rooms in the system
        >>> all_laundry = l.all_status()
        """
        laundry_rooms = {}
        for room in self.hall_to_link:
            laundry_rooms[room] = self.parse_a_hall(room)

        return laundry_rooms

    def hall_status(self, hall_id):
        """Return the status of each specific washer/dryer in a particular
        laundry room.
        :param hall_id:
             Integer corresponding to the id of the hall. This id
             is returned as part of the all_status call.
        >>> english_house = l.hall_status("English%20House")
        """
        if hall_id not in self.id_to_hall:
            raise ValueError("No hall with id %s exists." % hall_id)

        hall_name = self.id_to_hall[hall_id]
        location = self.id_to_location[hall_id]
        machines = self.parse_a_hall(hall_name)

        return {"machines": machines, "hall_name": hall_name, "location": location}

    def check_is_working(self):
        """ Returns True if the wash alert web interface seems to be
        working properly, or False otherwise.
        >>> l.check_is_working()
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

    # this function does not work
    '''
    def machine_usage(self, hall_no):
        """Returns the average usage of laundry machines every hour
        for a given hall.
        The usages are returned in a dictionary, with the key being
        the day of the week, and the value being an array listing the usages
        per hour.
        :param hall_no:
             integer corresponding to the id number for the hall. Thus number
             is returned as part of the all_status call.
        >>> english_house = l.machine_usage(2)
        """

        try:
            num = int(hall_no)
        except ValueError:
            raise ValueError("Room Number must be integer")
        r = requests.get(USAGE_BASE_URL + str(num), timeout=60)
        parsed = BeautifulSoup(r.text, "html5lib")
        usage_table = parsed.find_all("table", width="504px")[0]
        rows = usage_table.find_all("tr")
        usages = {}
        for i, row in enumerate(rows):
            day = []
            hours = row.find_all("td")
            for hour in hours:
                day.append(self.busy_dict[str(hour["class"][0])])
            usages[self.days[i]] = day
        return usages
    '''

    def save_data(self):
        """Retrieves current laundry info and saves it into the database."""

        now = timezone.localtime()

        if LaundrySnapshot.objects.filter(date=now).count() == 0:
            ids = {x["hall_name"]: x["id"] for x in self.hall_id_list}
            data = self.all_status()

            for name, room in data.items():
                LaundrySnapshot.objects.create(
                    hall_id=ids[name],
                    date=now,
                    available_washers=room["washers"]["open"],
                    available_dryers=room["dryers"]["open"],
                    total_washers=sum(
                        [room["washers"][x] for x in ["open", "running", "offline", "out_of_order"]]
                    ),
                    total_dryers=sum(
                        [room["dryers"][x] for x in ["open", "running", "offline", "out_of_order"]]
                    ),
                )
