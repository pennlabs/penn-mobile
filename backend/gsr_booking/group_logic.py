import random

from django.contrib.auth import get_user_model

from gsr_booking.api_wrapper import APIError, BookingWrapper
from gsr_booking.models import GSR, GroupMembership, Reservation


# GroupMembership


User = get_user_model()


class GroupBook:
    def __init__(self):
        self.bw = BookingWrapper()

    # def get_wharton_ids(self, group):
    #     wharton_members = GroupMembership.objects.filter(group=group,
    #   is_wharton=True).values_list(
    #         "user", flat=True
    #     )
    #     # shuffle to prevent sequential booking
    #     random.shuffle(wharton_members)
    #     return wharton_members

    # def get_all_ids(self, group):
    #     all_members = list(
    #         GroupMembership.objects.filter(group=group).values_list("user", flat=True)
    #     )
    #     # shuffle to prevent sequential booking
    #     random.shuffle(all_members)
    #     return all_members

    def get_wharton_users(self, group):
        wharton_users = []
        for member in group.members.all():
            if self.bw.is_wharton(member.username):
                wharton_users.append(member)
        random.shuffle(wharton_users)
        return wharton_users

    def book_room(self, gid, rid, room_name, start, end, user, group):

        # # TODO: check credits
        # gsr = GSR.objects.filter(gid=gid).first()
        # if not gsr:
        #     raise APIError(f"Unknown GSR GID {gid}")

        # if gsr.kind == GSR.KIND_WHARTON:
        #     wharton_ids = self.get_wharton_ids(group)
        #     for wharton_id in wharton_ids:
        #         # check credits here instead of booking
        #         try:
        #             self.bw.book_room(
        #                 gid, rid, room_name, start, end, User.objects.get(id=wharton_id)
        #             )
        #             Reservation.objects.create(start=start, end=end, creator=user, group=group)
        #             break
        #         except APIError:
        #             pass
        wharton_users = self.get_wharton_users(group)
        for wharton_user in wharton_users:
            try:
                self.bw.book_room(gid, rid, room_name, start, end, wharton_user)
                Reservation.objects.create(start=start, end=end, creator=user, group=group)
                break
            except APIError:
                pass

    def get_availability(self, lid, gid, start, end, user, group):
        gsr = GSR.objects.filter(gid=gid).first()
        if gsr.kind == GSR.KIND_WHARTON:
            # # check if wharton users is non-empty
            # wharton_id = self.get_wharton_ids(group)[0]
            # return self.bw.get_availability(lid, gid, start, end, User.objects.get(id=wharton_id))
            # wharton_user = self.get_wharton_users(group)[0]
            wharton_user = GroupMembership.objects.filter(group=group, is_wharton=True).first().user
            return self.bw.get_availability(lid, gid, start, end, wharton_user)
