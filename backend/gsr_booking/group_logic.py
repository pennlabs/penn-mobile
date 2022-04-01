import random
from types import MemberDescriptorType

from django.contrib.auth import get_user_model
from django.db.models import Prefetch

from gsr_booking.api_wrapper import APIError, BookingWrapper
from gsr_booking.models import GSR, Group, GroupMembership, Reservation


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

    def rebooking(self, user, time, enum):
        memberships = GroupMembership.objects.filter(user=user).select_related("group").all()
        group_ids = memberships.values_list("group", flat=True).distinct()
        # iterating thru each User in all corresponding Group objects
        # random ordering to prevent clustering
        for group in Group.objects.filter(id__in=group_ids).order_by("?"):
            for user in group.members.all().order_by("?"):
                # if check credits: user, enum

                print(user)

        if time != 0:
            # return failure
            pass

    def book_room(self, gid, rid, room_name, start, end, user, group):
        """
        Book function for Group
        """
        # TODO: check credits
        gsr = GSR.objects.filter(gid=gid).first()
        if not gsr:
            raise APIError(f"Unknown GSR GID {gid}")

        try:
            if gsr.kind == GSR.KIND_WHARTON:
                wharton_users = self.get_wharton_users(group)
                for wharton_user in wharton_users:
                    booking = self.bw.book_room(
                        gid, rid, room_name, start, end, wharton_user.user, group_book=True
                    )
                    break
            else:
                all_users = self.get_all_users(group)
                for all_user in all_users:
                    booking = self.bw.book_room(
                        gid, rid, room_name, start, end, all_user.user, group_book=True
                    )
                    break
            reservation = Reservation.objects.create(
                start=start, end=end, creator=user, group=group
            )
            booking.reservation = reservation
            booking.save()
        except APIError:
            pass

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
