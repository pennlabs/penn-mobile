from analytics.entries import ViewEntry
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game, LeaderboardEntry
from games.serializers import GameSerializer, LeaderboardEntrySerializer
from games.validators import validate_words_for_game
from pennmobile.analytics import LabsAnalytics


@LabsAnalytics.record_apiview(
    ViewEntry(name="game-today"),
)
class TodayGameView(APIView):
    """
    GET: returns the game board for the day
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        game = Game.get_today()
        if not game:
            return Response({"error": "No game found for today."}, status=404)
        return Response(GameSerializer(game).data)


@LabsAnalytics.record_apiview(
    ViewEntry(name="game-by-date"),
)
class GameByDateView(APIView):
    """
    GET: returns the game board for a specific date
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        game = get_object_or_404(Game, date=date)
        return Response(GameSerializer(game).data)


@LabsAnalytics.record_apiview(
    ViewEntry(name="leaderboard-by-date"),
)
class LeaderboardByDateView(APIView):
    """
    GET: returns the leaderboard for a specific date
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        game = get_object_or_404(Game, date=date)
        entries = game.scores.all()
        return Response(LeaderboardEntrySerializer(entries, many=True).data)


@LabsAnalytics.record_apiview(
    ViewEntry(name="submit-score"),
)
class SubmitScoreView(APIView):
    """
    POST: submits the authenticated user's score for a specific date
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, date):
        game = get_object_or_404(Game, date=date)
        score = request.data.get("score")
        words_found = request.data.get("words_found")

        if score is None or words_found is None:
            return Response({"error": "score and words_found are required."}, status=400)

        if (
            not isinstance(score, int)
            or not isinstance(words_found, int)
            or score < 0
            or words_found < 0
        ):
            return Response(
                {"error": "score and words_found must be non-negative integers."}, status=400
            )

        if LeaderboardEntry.objects.filter(game=game, user=request.user).exists():
            return Response({"error": "Score already submitted for this game."}, status=400)

        entry = LeaderboardEntry.objects.create(
            game=game,
            user=request.user,
            score=score,
            words_found=words_found,
        )
        return Response(LeaderboardEntrySerializer(entry).data, status=201)


@LabsAnalytics.record_apiview(
    ViewEntry(name="validate-game-log"),
)
class ValidateGameLogView(APIView):
    """
    POST: returns whether the words chosen are valid
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, date):
        game = get_object_or_404(Game, date=date)
        submitted_words = request.data.get("words", [])

        result = validate_words_for_game(game, submitted_words)
        if not result["valid"]:
            return Response(result, status=400)

        return Response({"valid": True}, status=200)
