from django.urls import path

from portal.views import CreatePoll, CreatePollOptions, RetrievePolls, UpdatePoll


urlpatterns = [
    path("polls/create/poll/", CreatePoll.as_view()),
    path("polls/create/option/", CreatePollOptions.as_view()),
    path("polls/update/poll/<pk>/", UpdatePoll.as_view()),
    path("polls/view/", RetrievePolls.as_view()),
]
