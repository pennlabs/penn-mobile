from analytics.entries import ViewEntry
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from games.models import Game, GameUser, GameUserTag, LeaderboardEntry
from games.serializers import GameSerializer, LeaderboardEntrySerializer
from pennmobile.analytics import LabsAnalytics


LEADERBOARD_SORT_FIELDS = ("score", "num_words_found", "submitted_at")


def is_opted_in(user):
    game_user = getattr(user, "gameuser", None)
    return bool(game_user and game_user.show_name)


def serialize_entry(entry, show_names):
    return LeaderboardEntrySerializer(entry, context={"show_names": show_names}).data


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
        entries = entries.filter(
            user__gameuser__tags__kind=GameUserTag.SCHOOL,
            user__gameuser__tags__value__in=schools,
        ).distinct()
    if majors := params.getlist("major"):
        entries = entries.filter(
            user__gameuser__tags__kind=GameUserTag.MAJOR,
            user__gameuser__tags__value__in=majors,
        ).distinct()
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
        visible = entries.filter(user__gameuser__show_name=True)
        top = visible
        if (limit := request.query_params.get("limit")) is not None:
            if not limit.isdigit():
                return Response({"detail": "limit must be a non-negative integer."}, status=400)
            top = visible[: int(limit)]
        top = list(top)
        assign_ranks(top, field)

        show_names = is_opted_in(request.user)
        payload = {
            "leaderboard": LeaderboardEntrySerializer(
                top, many=True, context={"show_names": show_names}
            ).data,
            "me": None,
        }
        mine = next((entry for entry in top if entry.user_id == request.user.pk), None)
        if mine is None:
            mine = entries.filter(user=request.user).first()
            if mine:
                ranking = visible if is_opted_in(request.user) else entries
                mine.rank = rank_for(ranking, mine, field, descending)
        if mine is not None:
            payload["me"] = serialize_entry(mine, show_names=is_opted_in(mine.user))
        return Response(payload)


@LabsAnalytics.record_apiview(
    ViewEntry(name="submit-score"),
)
class SubmitScoreView(APIView):
    """
    POST: validates submitted words, computes score, and saves leaderboard entry

    Body:
        words: list of words found on the board
        show_name: if present, opt in or out of the named leaderboard
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

        show_name = request.data.get("show_name") is True if "show_name" in request.data else None
        game_user = GameUser.sync_from_platform(request.user, show_name=show_name)

        score = sum((len(w) - 2) ** 2 * 100 for w in normalized)

        entry = LeaderboardEntry.objects.create(
            game=game,
            user=request.user,
            score=score,
            num_words_found=len(normalized),
        )
        return Response(serialize_entry(entry, show_names=game_user.show_name), status=201)
