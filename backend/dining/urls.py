from django.urls import path

from dining.views import Menus, Venues


urlpatterns = [
    path("venues/", Venues.as_view(), name="venues"),
    path("menus/", Menus.as_view(), name="menus"),
    path("menus/<date>/", Menus.as_view(), name="menus-with-date"),
]
