from django.urls import path
from rest_framework import routers

from portal.views import (
    PollOptions,
    Polls,
    PollVotes,
    PollVoteStatistics,
    RetrievePollVotes,
    TargetPopulations,
)


router = routers.DefaultRouter()
router.register(r"polls", Polls, basename="poll")
router.register(r"options", PollOptions, basename="polloption")
router.register(r"votes", PollVotes, basename="pollvote")

additional_urls = [
    path("poll-history/", RetrievePollVotes.as_view(), name="poll-history"),
    path("populations/", TargetPopulations.as_view(), name="target-populations"),
    path("vote-statistics/<id>/", PollVoteStatistics.as_view(), name="vote-time-series"),
]
urlpatterns = router.urls + additional_urls
