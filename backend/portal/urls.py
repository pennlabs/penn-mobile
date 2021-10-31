from django.urls import path
from rest_framework import routers

from portal.views import (
    PollOptions,
    Polls,
    PollVotes,
    PollVoteStatistics,
    Posts,
    RetrievePollVotes,
    TargetPopulations,
)


app_name = "portal"

router = routers.DefaultRouter()
router.register(r"polls", Polls, basename="poll")
router.register(r"options", PollOptions, basename="polloption")
router.register(r"votes", PollVotes, basename="pollvote")
router.register(r"poll-history", RetrievePollVotes, basename="poll-history")
router.register(r"posts", Posts, basename="posts")

additional_urls = [
    path("populations/", TargetPopulations.as_view(), name="target-populations"),
    path("vote-statistics/<id>/", PollVoteStatistics.as_view(), name="vote-statistics"),
]
urlpatterns = router.urls + additional_urls
