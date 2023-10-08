from django.urls import path
from django.views.decorators.cache import cache_page

from laundry.views import HallInfo, HallUsage, Ids, MultipleHallInfo, Preferences, Status
from utils.cache import Cache


urlpatterns = [
    path("hall/<hall_id>/", cache_page(Cache.MINUTE)(HallInfo), name="hall-info",),
    path("usage/<hall_id>/", cache_page(Cache.MINUTE)(HallUsage), name="hall-usage",),
    path(
        "rooms/<hall_ids>",
        cache_page(Cache.MINUTE)(MultipleHallInfo),
        name="multiple-hall-info",
    ),
    path("halls/ids/", cache_page(Cache.MONTH)(Ids), name="hall-ids",),
    path("status/", Status.as_view(), name="status"),
    path("preferences/", Preferences.as_view(), name="preferences"),
]
