from django.urls import path

from penndata.views import Analytics, Calendar, Events, Fitness, HomePage, HomePageOrdering, News


urlpatterns = [
    path("news/", News.as_view(), name="news"),
    path("calendar/", Calendar.as_view(), name="calendar"),
    path("homepage", HomePage.as_view(), name="homepage"),
    path("events/<type>/", Events.as_view(), name="events"),
    path("order/", HomePageOrdering.as_view(), name="home-page-order"),
    path("fitness/", Fitness.as_view(), name="fitness"),
    path("analytics/", Analytics.as_view(), name="analytics"),
]
