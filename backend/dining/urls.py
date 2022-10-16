from django.urls import path

from dining.views import Menus, Preferences, Venues


urlpatterns = [
    path("venues/", Venues.as_view(), name="venues"),
    path("menus/", Menus.as_view(), name="menus"),
    path("menus/<date>/", Menus.as_view(), name="menus-with-date"),
    path("preferences/", Preferences.as_view(), name="dining-preferences"),
]
