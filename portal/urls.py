from django.urls import include, path
from rest_framework import routers

from portal.views import (
    CreatePoll,
    CreatePollOptions,
    CreatePollVote,
    RetrievePolls,
    RetrievePollVotes,
    UpdatePoll,
    UpdatePollOption,
    UpdatePollVote,
)


router = routers.DefaultRouter()
router.register(r"polls/view", RetrievePolls)

additional_urls = [
    path("", include(router.urls)),
    path("polls/create/poll/", CreatePoll.as_view(), name="create-poll"),
    path("polls/update/poll/<pk>/", UpdatePoll.as_view(), name="update-poll"),
    path("polls/create/option/", CreatePollOptions.as_view(), name="create-option"),
    path("polls/update/option/<pk>/", UpdatePollOption.as_view(), name="update-option"),
    path("polls/create/vote/", CreatePollVote.as_view(), name="create-vote"),
    path("polls/update/vote/<pk>/", UpdatePollVote.as_view(), name="update-vote"),
    path("polls/history/", RetrievePollVotes.as_view(), name="poll-history"),
]

urlpatterns = router.urls + additional_urls
