from django.urls import path

from laundry import views

urlpatterns = [

    path("halls/", views.Halls.as_view(), name="halls"),
    path("halls/<hall_id>/", views.HallStatus.as_view(), name="hall-status"),
    path("halls/<hall_id>/usage/", views.HallUsage.as_view(), name="hall-usage"),

]
