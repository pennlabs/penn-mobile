from django.urls import path
from django.views.decorators.cache import cache_page

from laundry.views import HallInfo, HallUsage, Ids, MultipleHallInfo, Preferences, Status
from utils.cache import MINUTE_IN_SECONDS, MONTH_IN_SECONDS_APPROX


urlpatterns = [
    path("hall/<hall_id>/", cache_page(MINUTE_IN_SECONDS)(HallInfo), name="hall-info",),
    path("usage/<hall_id>/", cache_page(MINUTE_IN_SECONDS)(HallUsage), name="hall-usage",),
    path(
        "rooms/<hall_ids>",
        cache_page(MINUTE_IN_SECONDS)(MultipleHallInfo),
        name="multiple-hall-info",
    ),
    path("halls/ids/", cache_page(MONTH_IN_SECONDS_APPROX)(Ids), name="hall-ids",),
    path("status/", cache_page(30)(Status), name="status",),
    path("preferences/", Preferences.as_view(), name="preferences"),
]
