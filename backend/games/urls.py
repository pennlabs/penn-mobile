from django.urls import path

from games.views import GameByDateView, LeaderboardByDateView, SubmitScoreView, TodayGameView


urlpatterns = [
    path("word-hunt/today/", TodayGameView.as_view(), name="word-hunt-today"),
    path("word-hunt/<date>/", GameByDateView.as_view(), name="word-hunt-by-date"),
    path(
        "word-hunt/<date>/leaderboard/",
        LeaderboardByDateView.as_view(),
        name="word-hunt-leaderboard-by-date",
    ),
    path("word-hunt/<date>/submit/", SubmitScoreView.as_view(), name="word-hunt-submit-score"),
]
