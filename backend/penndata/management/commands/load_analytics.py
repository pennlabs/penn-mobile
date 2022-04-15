from datetime import datetime

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from penndata.models import AnalyticsEvent


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        analytics_objects = []

        # read in file and convert into array
        df = pd.read_csv("penndata/management/account.csv", header=None)
        np_arr = df.to_numpy()

        user_dict = dict()

        # create mapping from pennkey to User to
        # avoid db calls in the main loop of the function
        for user in User.objects.all():
            user_dict[user.username] = user

        for row in np_arr:
            # iterate thru csv and add to list
            pennkey, created_at, cell_type, index, is_interaction, misc_2, data, misc_3 = row

            # skips if User object not present
            if pennkey not in user_dict:
                continue

            # cleans csv data
            user = user_dict[pennkey]
            date_object = make_aware(datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S.%f"))
            data = None if data == "NULL" else data
            is_interaction = True if is_interaction == 1 else False

            analytics_objects.append(
                AnalyticsEvent(
                    user=user,
                    created_at=date_object,
                    cell_type=cell_type,
                    index=index,
                    is_interaction=is_interaction,
                    data=data,
                )
            )

        # bulk creates objects at once
        AnalyticsEvent.objects.bulk_create(analytics_objects)

        self.stdout.write("Uploaded Analytics Events!")
