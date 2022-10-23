import datetime
import random

from django.contrib.auth import get_user_model

from gsr_booking.api_wrapper import APIError, BookingWrapper, CreditType
from gsr_booking.models import GSR, GroupMembership, Reservation


User = get_user_model()


class GroupBook:
    def __init__(self):
        self.bw = BookingWrapper()

    def get_wharton_users(self, group):
        """
        Returns list of wharton users of a Group in random ordering
        """
        # TODO: filter for pennkey allowed
        wharton_users = list(GroupMembership.objects.filter(group=group, is_wharton=True))
        # shuffle to prevent sequential booking
        random.shuffle(wharton_users)
        return wharton_users

    def get_all_users(self, group):
        """
        Returns list of all users of a Group in random ordering
        """
        # TODO: filter for pennkey allowed
        all_users = list(GroupMembership.objects.filter(group=group))
        # shuffle to prevent sequential booking
        random.shuffle(all_users)
        return all_users

    def book_room(self, gid, rid, room_name, start, end, user, group):
        """
        Book function for Group
        """
        # TODO: check credits
        gsr = GSR.objects.filter(gid=gid).first()
        if not gsr:
            raise APIError(f"Unknown GSR GID {gid}")

        start = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S%z")
        end = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z")

        if gsr.kind == GSR.KIND_WHARTON:
            users = self.get_wharton_users(group)
            credit_id = gsr.lid
        else:
            users = self.get_all_users(group)
            credit_id = CreditType.LIBCAL.value

        total_credits = sum([self.bw.check_credits(usr.user).get(credit_id, 0) for usr in users])
        duration = int((end.timestamp() - start.timestamp()) / 60)
        if total_credits < duration:
            raise APIError("Not Enough Credits to Book")
        if duration % 30 != 0:
            raise APIError("Invalid duration")

        reservation = Reservation.objects.create(start=start, end=end, creator=user, group=group)
        while duration > 0:
            for usr in users:
                credit = self.bw.check_credits(usr.user).get(credit_id, 0)
                if credit < 30:
                    continue
                curr_end = start + datetime.timedelta(minutes=30)
                booking = self.bw.book_room(
                    gid,
                    rid,
                    room_name,
                    start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    curr_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    usr.user,
                    group_book=True,
                )
                booking.reservation = reservation
                booking.save()
                start = curr_end
                duration -= 30
                if duration <= 0:
                    break
        return reservation

        #         try:
        #             booking = self.bw.book_room(
        #                 gid, rid, room_name, start, end, wharton_user.user, group_book=True
        #             )
        #             reservation = Reservation.objects.create(
        #                 start=start, end=end, creator=user, group=group
        #             )
        #             booking.reservation = reservation
        #             booking.save()
        #             break
        #         except APIError:
        #             pass
        # else:
        #     all_users = self.get_all_users(group)
        #     for all_user in all_users:
        #         try:
        #             booking = self.bw.book_room(
        #                 gid, rid, room_name, start, end, all_user.user, group_book=True
        #             )
        #             reservation = Reservation.objects.create(
        #                 start=start, end=end, creator=user, group=group
        #             )
        #             booking.reservation = reservation
        #             booking.save()
        #             break
        #         except APIError:
        #             pass

    def get_availability(self, lid, gid, start, end, user, group):
        """
        Availability function for Group
        """

        gsr = GSR.objects.filter(gid=gid).first()
        if gsr.kind == GSR.KIND_WHARTON:
            # check if wharton users is non-empty
            wharton_user = GroupMembership.objects.filter(group=group, is_wharton=True).first()
            if wharton_user:
                return self.bw.get_availability(lid, gid, start, end, wharton_user.user)

        return self.bw.get_availability(lid, gid, start, end, user)
