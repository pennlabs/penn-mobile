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
urlpatterns = [
    path("", include(router.urls)),
    path("polls/create/poll/", CreatePoll.as_view()),
    path("polls/create/option/", CreatePollOptions.as_view()),
    path("polls/update/option/<pk>/", UpdatePollOption.as_view()),
    path("polls/update/poll/<pk>/", UpdatePoll.as_view()),
    path("polls/create/vote/", CreatePollVote.as_view()),
    path("polls/update/vote/<pk>/", UpdatePollVote.as_view()),
    path("polls/history/", RetrievePollVotes.as_view()),
]
