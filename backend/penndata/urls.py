from django.urls import path
from django.views.decorators.cache import cache_page
from backend.utils.cache import MINUTE_IN_SECONDS, MONTH_IN_SECONDS_APPROX

from penndata.views import (
    Analytics,
    Calendar,
    Events,
    FitnessPreferences,
    FitnessRoomView,
    FitnessUsage,
    HomePage,
    HomePageOrdering,
    News,
    UniqueCounterView,
)


urlpatterns = [
    path(
        "news/",
        cache_page(5 * MINUTE_IN_SECONDS)(News),
        name="news",
    ),
    path(
        "calendar/",
        cache_page(5 * MINUTE_IN_SECONDS)(Calendar),
        name="calendar",
    ),
    path("homepage", HomePage.as_view(), name="homepage"),
    path("events/<type>/", Events.as_view(), name="events"),
    path(
        "order/",
        cache_page(MONTH_IN_SECONDS_APPROX)(HomePageOrdering),
        name="home-page-order",
    ),
    path(
        "fitness/rooms/",
        cache_page(MINUTE_IN_SECONDS)(FitnessRoomView),
        name="fitness",
    ),
    path(
        "fitness/usage/<room_id>/",
        cache_page(MINUTE_IN_SECONDS)(FitnessUsage),
        name="fitness-usage",
    ),
    path(
        "fitness/preferences/", FitnessPreferences.as_view(), name="fitness-preferences"
    ),
    path("analytics/", Analytics.as_view(), name="analytics"),
    path(
        "eventcount/",
        cache_page(MINUTE_IN_SECONDS)(UniqueCounterView.as_view()),
        name="eventcounter",
    ),
]
