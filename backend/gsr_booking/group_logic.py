import random

from gsr_booking.api_wrapper import APIError, BookingWrapper
from gsr_booking.models import GSR


class GroupBook:
    def __init__(self):
        self.bw = BookingWrapper()

    def get_wharton_users(self, group):
        wharton_users = []
        for member in group.members.all():
            if self.bw.is_wharton(member.username):
                wharton_users.append(member)
        # shuffle to prevent sequential booking
        random.shuffle(wharton_users)
        return wharton_users

    def book_room(self, gid, rid, room_name, start, end, user, group):

        # TODO: check credits
        gsr = GSR.objects.filter(gid=gid).first()
        if gsr.kind == GSR.KIND_WHARTON:
            wharton_users = self.get_wharton_users(group)
            for wharton_user in wharton_users:
                # check credits here instead of booking
                try:
                    self.bw.book_room(gid, rid, room_name, start, end, wharton_user)
                    break
                except APIError:
                    pass

    def get_availability(self, lid, gid, start, end, user, group):
        gsr = GSR.objects.filter(gid=gid).first()
        if gsr.kind == GSR.KIND_WHARTON:
            # check if wharton users is non-empty
            wharton_user = self.get_wharton_users(group)[0]
            return self.bw.get_availability(lid, gid, start, end, wharton_user)
