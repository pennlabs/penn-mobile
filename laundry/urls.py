from django.urls import path

from laundry.views import (
    HallInfo,
    Halls,
    HallUsage,
    Ids,
    MultipleHallInfo,
    Preferences,
    Status,
    TwoHalls,
)


urlpatterns = [
    path("halls/", Halls.as_view(), name="halls"),
    path("hall/<hall_id>/", HallInfo.as_view(), name="hall-info"),
    path("usage/<hall_id>/", HallUsage.as_view(), name="hall-usage"),
    path("rooms/<hall_ids>", MultipleHallInfo.as_view(), name="multiple-hall-info"),
    path("hall/<hall_id1>/<hall_id2>/", TwoHalls.as_view(), name="two-hall-info"),
    path("halls/ids/", Ids.as_view(), name="hall-ids"),
    path("status/", Status.as_view(), name="status"),
    path("preferences/", Preferences.as_view(), name="preferences"),
]
