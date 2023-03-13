from django.urls import path

from penndata.views import (
    Analytics,
    Calendar,
    Events,
    Fitness,
    FitnessUsage,
    HomePage,
    HomePageOrdering,
    News,
    UniqueCounterView,
)


urlpatterns = [
    path("news/", News.as_view(), name="news"),
    path("calendar/", Calendar.as_view(), name="calendar"),
    path("homepage", HomePage.as_view(), name="homepage"),
    path("events/<type>/", Events.as_view(), name="events"),
    path("order/", HomePageOrdering.as_view(), name="home-page-order"),
    path("fitness/", Fitness.as_view(), name="fitness"),
    path("fitness/usage/<room_id>/", FitnessUsage.as_view(), name="fitness-usage"),
    path("analytics/", Analytics.as_view(), name="analytics"),
    path("eventcount/", UniqueCounterView.as_view(), name="eventcounter"),
]
