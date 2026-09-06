from analytics.entries import ViewEntry
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game, LeaderboardEntry
from games.serializers import GameSerializer, LeaderboardEntrySerializer
from pennmobile.analytics import LabsAnalytics


LEADERBOARD_SORT_FIELDS = ("score", "num_words_found", "submitted_at")


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

    Query params:
        sort: one of LEADERBOARD_SORT_FIELDS, optionally prefixed with "-" (default "-score")
        limit: max number of entries to return (default all)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        game = get_object_or_404(Game, date=date)

        sort = request.query_params.get("sort", "-score")
        if sort.lstrip("-") not in LEADERBOARD_SORT_FIELDS:
            return Response(
                {"error": f"sort must be one of {list(LEADERBOARD_SORT_FIELDS)}."}, status=400
            )
        entries = game.scores.select_related("user").order_by(sort, "submitted_at")

        if (limit := request.query_params.get("limit")) is not None:
            if not limit.isdigit():
                return Response({"error": "limit must be a non-negative integer."}, status=400)
            entries = entries[: int(limit)]

        return Response(LeaderboardEntrySerializer(entries, many=True).data)


@LabsAnalytics.record_apiview(
    ViewEntry(name="submit-score"),
)
class SubmitScoreView(APIView):
    """
    POST: validates submitted words, computes score, and saves leaderboard entry

    Body:
        words: list of words found on the board
        show_name: opt in to showing your name on the leaderboard (default False)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, date):
        game = get_object_or_404(Game, date=date)
        submitted_words = request.data.get("words")

        if not isinstance(submitted_words, list):
            return Response({"error": "words must be a list."}, status=400)

        normalized = [w.lower().strip() for w in submitted_words]

        if len(normalized) != len(set(normalized)):
            return Response({"error": "Duplicate words submitted."}, status=400)

        legal_words = set(game.possible_words)
        if any(w not in legal_words for w in normalized):
            invalid = [w for w in normalized if w not in legal_words]
            return Response(
                {"error": "Invalid words submitted.", "invalid_words": invalid}, status=400
            )

        if LeaderboardEntry.objects.filter(game=game, user=request.user).exists():
            return Response({"error": "Score already submitted for this game."}, status=400)

        score = sum((len(w) - 2) ** 2 * 100 for w in normalized)

        entry = LeaderboardEntry.objects.create(
            game=game,
            user=request.user,
            score=score,
            num_words_found=len(normalized),
            show_name=request.data.get("show_name") is True,
        )
        return Response(LeaderboardEntrySerializer(entry).data, status=201)
