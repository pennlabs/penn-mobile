from django.urls import path
from django.views.decorators.cache import cache_page

from games.views import TodayGameView, GameByDateView, LeaderboardByDateView, SubmitScoreView, ValidateGameLogView


urlpatterns = [
    path("today/", TodayGameView.as_view(), name="game-today"),
    path("<date>/", GameByDateView.as_view(), name="game-by-date"),
    path("<date>/leaderboard/", LeaderboardByDateView.as_view(), name="game-leaderboard-by-date"),
    path("<date>/submit/", SubmitScoreView.as_view(), name="submit-score"),
    path("<date>/validate/", ValidateGameLogView.as_view(), name="validate-game-log"),
]