import requests
import datetime
import math
import random


class BookingLogic:

    DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%S%z"
    MAX_SLOT_HRS = 2.0  # the longest booking allowed per person
    MIN_SLOT_HRS = 0.5  # the minimum booking allowed per person
    
    def book_room_for_group(self, group, is_wharton, room, lid, start, end, requester_pennkey):
        # makes a request to labs api server to book rooms, and returns result json if successful
        members = group.get_pennkey_active_members()
        if len(members) < 1:
            return {
                "complete_success": False,
                "partial_success": False,
                "error": "No members in the group have enabled their pennkey to be used for group bookings"
            }

        #randomize order, and put requester first in the order
        random.shuffle(members)
        for (i, member) in enumerate(members): #puts the requester as the first person
            if (member['username'] == requester_pennkey):
                temp = members[0]
                members[0] = member
                members[i] = temp
                break

        if is_wharton:  # huntsman reservation
            return {"complete_success": False, "partial_success": False, "error": "Unable to book huntsman rooms yet"}
        else:  # lib reservation
            #Find the first timeslot to book for (next_start, next_end)
            START_DATE = datetime.datetime.strptime(start, self.DATE_FORMAT_STR)
            END_DATE = datetime.datetime.strptime(end, self.DATE_FORMAT_STR)
            next_start = START_DATE
            next_end = min(END_DATE, next_start + datetime.timedelta(hours=self.MAX_SLOT_HRS))

            # loop through each member, and attempt to book on their behalf
            bookings = {}
            failed_members = []  #store the members w/ failed bookings in here

            for member in members:
                if next_end - next_start < datetime.timedelta(hours=0.1):
                    break
                if member['user__email'] is "":
                    continue

                # make request to labs-api-server
                success, error = self.book_room_for_user(
                    room,
                    lid,
                    next_start.strftime(self.DATE_FORMAT_STR),
                    next_end.strftime(self.DATE_FORMAT_STR),
                    member['user__email'],
                )
                if success:
                    key = f'{lid}_{room}' 
                    if not key in bookings:
                        bookings[key] = []
                    new_bookings = self.split_booking(next_start, next_end, member['username'], True)
                    bookings[key].extend(new_bookings)
                    
                    next_start = next_end
                    next_end = min(END_DATE, next_start + datetime.timedelta(hours=self.MAX_SLOT_HRS))
                elif self.is_fatal_error(error):
                    result_json = self.construct_bookings_json_obj(bookings, lid, room, END_DATE, next_start, next_end, error)
                    return result_json
                else:
                    failed_members.append(member)

            # if unbooked slots still remain and not all booking requests succeeded, loop through each member again
            # but get reservation credits first to see how much we can book
            
            for member in failed_members:
                if next_end - next_start < datetime.timedelta(hours=0.1):
                    print("BOOKED EVERYTHING ALREADY")
                    break
                if member['user__email'] is "":
                    print("empty email address")
                    continue

                # calculate number of credits already used via getReservations
                (success, used_credit_hours) = self.get_used_booking_credit_for_user(lid, member['user__email'])
                remaining_credit_hours = self.MAX_SLOT_HRS - used_credit_hours
                rounded_remaining_credit_hours = math.floor(2 * remaining_credit_hours) / 2
                if success and remaining_credit_hours >= self.MIN_SLOT_HRS:
                    next_end = min(
                        END_DATE,
                        next_start + datetime.timedelta(hours=rounded_remaining_credit_hours),
                    )
                    (success, error) = self.book_room_for_user(
                        room,
                        lid,
                        next_start.strftime(self.DATE_FORMAT_STR),
                        next_end.strftime(self.DATE_FORMAT_STR),
                        member['user__email'],
                    )
                    if success:
                        key = f'{lid}_{room}' 
                        if not key in bookings:
                            bookings[key] = []
                        new_bookings = self.split_booking(next_start, next_end, member['username'], True)
                        bookings[key].extend(new_bookings)

                        next_start = next_end
                        next_end = min(
                            END_DATE, next_start + datetime.timedelta(hours=MAX_SLOT_HRS)
                        )
                    elif self.is_fatal_error(error):
                        result_json = self.construct_bookings_json_obj(bookings, lid, room, END_DATE, next_start, next_end, error)
                        return result_json
            result_json = self.construct_bookings_json_obj(bookings, lid, room, END_DATE, next_start, next_end, error)
            return result_json
    def is_fatal_error(self, error):
        #consider all errors fatal unless its a daily limit error
        if error is not None:
            if ('daily limit'.lower() not in error.lower()):
                return False
            return True
        return False

    def construct_bookings_json_obj(self, succesful_bookings, lid, room, end, next_start, next_end, error):
        #takes in a set of bookings and constructs a JSON object from them (after pre-processing)
        bookings = succesful_bookings
        complete_success = (next_end - next_start < datetime.timedelta(hours=0.1)) and (error is None)
        partial_success = (len(bookings) > 0)
        result_json = {
            "complete_success": complete_success,
            "partial_success": partial_success,
            "rooms": []
        }

        #add failed bookings to bookings
        failed_bookings = self.split_booking(next_start, end, None, False)
        failed_key = f'{lid}_{room}' 
        if not failed_key in bookings:
            bookings[failed_key] = []
        failed_split_bookings = self.split_booking(next_start, next_end, None, False)
        bookings[failed_key].extend(failed_split_bookings)

        #add successful bookings to result_json
        for (key, bookings_array) in bookings.items():
            key_split = key.split('_')
            lid = key_split[0]
            room = key_split[1]
            result_json['rooms'].append({
                'lid': lid,
                'room': room,
                'bookings': bookings_array
            })

        #handle potential error
        if error is not None:
            if "not a valid".lower() in error.lower():
                result_json['error'] = 'Attempted to book for an invalid time slot'
            elif "daily limit".lower() in error.lower():
                result_json['error'] = 'Group does not have sufficient booking credits'
            else:
                result_json['error'] = str(error)
        return result_json    

        

    def get_used_booking_credit_for_user(self, lid, email):
        # returns a user's used booking credit (in hours) for a specific building (lid)
        RESERVATIONS_URL = "https://api.pennlabs.org/studyspaces/reservations"
        if lid == "1":
            return (False, 0)  # doesn't support huntsman yet
        try:
            r = requests.get(RESERVATIONS_URL + "?email=" + email)
            if r.status_code == 200:
                resp_data = r.json()
                reservations = resp_data["reservations"]
                used_credit_hours = 0
                for reservation in reservations:
                    from_date = datetime.datetime.strptime(reservation["fromDate"], self.DATE_FORMAT_STR)
                    to_date = datetime.datetime.strptime(reservation["toDate"], self.DATE_FORMAT_STR)
                    reservation_hours = (to_date - from_date).total_seconds() / 3600
                    if str(reservation["lid"]) == lid and reservation_hours > 0.1:
                        used_credit_hours += reservation_hours
                return (True, used_credit_hours)
        except requests.exceptions.RequestException as e:
            print(e)
        return (False, 0)

    def split_booking(self, start, end, pennkey, booked):
        # splits a booking into smaller bookings (of min_slot_hrs) for displaying to user
        bookings = []
        temp_start = start
        temp_end = temp_start + datetime.timedelta(hours=self.MIN_SLOT_HRS)
        while (end - temp_start >= datetime.timedelta(hours=self.MIN_SLOT_HRS)):
            booking_obj = {
                'start': temp_start.strftime(self.DATE_FORMAT_STR), 
                'end': temp_end.strftime(self.DATE_FORMAT_STR), 
                'booked': booked
            }
            if pennkey is not None:
                booking_obj['pennkey'] = pennkey
            bookings.append(booking_obj)
            temp_start = temp_end
            temp_end += datetime.timedelta(hours=self.MIN_SLOT_HRS)
        return bookings

    def book_room_for_user(self, room, lid, start, end, email):
        # tries to make a booking for an individual user, and returns success or not (and the error) in a tuple
        if lid is "1":
            return False  # does not support huntsman booking yet
        BOOKING_URL = "https://api.pennlabs.org/studyspaces/book"
        form_data = {
            "firstname": "Group GSR User",
            "lastname": "Group GSR User",
            "groupname": "Group GSR",
            "size": "2-3",
            "phone": "2158986533",
            "room": room,
            "lid": lid,
            "start": start,
            "end": end,
            "email": email,
        }

        try:
            r = requests.post(BOOKING_URL, data=form_data)
            if r.status_code == 200:
                resp_data = r.json()
                if "error" in resp_data and resp_data["error"] is not None:
                    return (False, resp_data["error"])
                return (resp_data["results"], None)
        except requests.exceptions.RequestException as e:
            print("error: " + str(e))
        return (False, None)