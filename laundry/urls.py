from django.urls import path

from laundry.views import HallInfo, Halls, HallUsage


urlpatterns = [
    path("halls/", Halls.as_view(), name="halls"),
    path("halls/<hall_id>/", HallInfo.as_view(), name="hall-info"),
    path("usage/<hall_id>/", HallUsage.as_view(), name="hall-usage"),
]
