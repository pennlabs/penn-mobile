from django.urls import path

from games.views import (
    GameByDateView,
    LeaderboardByDateView,
    SubmitScoreView,
    TodayGameView,
    ValidateGameLogView,
)


urlpatterns = [
    path("today/", TodayGameView.as_view(), name="game-today"),
    path("<date>/", GameByDateView.as_view(), name="game-by-date"),
    path("<date>/leaderboard/", LeaderboardByDateView.as_view(), name="game-leaderboard-by-date"),
    path("<date>/submit/", SubmitScoreView.as_view(), name="submit-score"),
    path("<date>/validate/", ValidateGameLogView.as_view(), name="validate-game-log"),
]
