from analytics.entries import ViewEntry
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game, GameUser, LeaderboardEntry
from games.serializers import GameSerializer, GameUserSerializer, LeaderboardEntrySerializer
from pennmobile.analytics import LabsAnalytics


LEADERBOARD_SORT_FIELDS = ("score", "num_words_found", "submitted_at")


def assign_ranks(entries, field):
    rank = 0
    previous = object()
    for index, entry in enumerate(entries, start=1):
        value = getattr(entry, field)
        if value != previous:
            rank = index
            previous = value
        entry.rank = rank


def rank_for(entries, entry, field, descending):
    lookup = f"{field}__gt" if descending else f"{field}__lt"
    return entries.filter(**{lookup: getattr(entry, field)}).count() + 1


def apply_leaderboard_filters(entries, params):
    if schools := params.getlist("school"):
        entries = entries.filter(user__gameuser__school__in=schools)
    if majors := params.getlist("major"):
        entries = entries.filter(user__gameuser__major__in=majors)
    if (year := params.get("year")) is not None:
        if not year.isdigit():
            return None, Response({"detail": "year must be a non-negative integer."}, status=400)
        entries = entries.filter(user__gameuser__graduation_year=int(year))
    return entries, None


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
            return Response({"detail": "No game found for today."}, status=404)
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
        limit: max number of opted-in entries to return (default all)
        school: filter by school name (repeatable)
        major: filter by major name (repeatable)
        year: filter by graduation year

    The public leaderboard only includes users who are not anonymized. The
    authenticated user's private result is returned separately in "me" and is
    ranked against all matching scores, including anonymized users.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, date):
        game = get_object_or_404(Game, date=date)

        sort = request.query_params.get("sort", "-score")
        if sort.lstrip("-") not in LEADERBOARD_SORT_FIELDS:
            return Response(
                {"detail": f"sort must be one of {list(LEADERBOARD_SORT_FIELDS)}."}, status=400
            )
        entries, error = apply_leaderboard_filters(
            game.scores.select_related("user__gameuser"), request.query_params
        )
        if error:
            return error
        field = sort.lstrip("-")
        descending = sort.startswith("-")
        entries = entries.order_by(sort, "submitted_at")
        visible = entries.filter(user__gameuser__anonymized=False)
        top = visible
        if (limit := request.query_params.get("limit")) is not None:
            if not limit.isdigit():
                return Response({"detail": "limit must be a non-negative integer."}, status=400)
            top = visible[: int(limit)]
        top = list(top)
        assign_ranks(top, field)

        payload = {
            "leaderboard": LeaderboardEntrySerializer(top, many=True).data,
            "me": None,
        }
        mine = entries.filter(user=request.user).first()
        if mine:
            mine.rank = rank_for(entries, mine, field, descending)
            payload["me"] = LeaderboardEntrySerializer(mine).data
        return Response(payload)


@LabsAnalytics.record_apiview(
    ViewEntry(name="game-user-profile"),
)
class GameUserProfileView(APIView):
    """GET or update the authenticated user's Word Hunt profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        game_user = GameUser.for_user(request.user)
        return Response(GameUserSerializer(game_user).data)

    def patch(self, request):
        serializer = GameUserSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        game_user = GameUser.for_user(
            request.user, anonymized=serializer.validated_data.get("anonymized")
        )
        game_user = GameUser.sync_from_platform(request.user)
        return Response(GameUserSerializer(game_user).data)


@LabsAnalytics.record_apiview(
    ViewEntry(name="submit-score"),
)
class SubmitScoreView(APIView):
    """
    POST: validates submitted words, computes score, and saves leaderboard entry

    Body:
        words: list of words found on the board
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, date):
        game = get_object_or_404(Game, date=date)
        submitted_words = request.data.get("words")

        if not isinstance(submitted_words, list):
            return Response({"detail": "words must be a list."}, status=400)

        normalized = [w.lower().strip() for w in submitted_words]

        if len(normalized) != len(set(normalized)):
            return Response({"detail": "Duplicate words submitted."}, status=400)

        legal_words = set(game.possible_words)
        if any(w not in legal_words for w in normalized):
            invalid = [w for w in normalized if w not in legal_words]
            return Response(
                {"detail": "Invalid words submitted.", "invalid_words": invalid}, status=400
            )

        if LeaderboardEntry.objects.filter(game=game, user=request.user).exists():
            return Response({"detail": "Score already submitted for this game."}, status=400)

        score = sum((len(w) - 2) ** 2 * 100 for w in normalized)

        entry = LeaderboardEntry.objects.create(
            game=game,
            user=request.user,
            score=score,
            num_words_found=len(normalized),
        )
        return Response(
            LeaderboardEntrySerializer(entry).data,
            status=201,
        )
