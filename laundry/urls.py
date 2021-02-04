from django.urls import path

from laundry import views


urlpatterns = [
    path("halls/", views.Halls.as_view(), name="halls"),
    path("halls/<hall_id>/", views.HallInfo.as_view(), name="hall-info"),
    path("usage/<hall_id>/", views.HallUsage.as_view(), name="hall-usage"),
]
