from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from presence import store
from presence.consent import get_consent
from presence.models import PresenceOptIn, Venue
from presence.serializers import (
    ConsentSerializer,
    HeartbeatSerializer,
    OptInSerializer,
    TokenResponseSerializer,
    TokenSerializer,
    VenueSerializer,
)


@extend_schema(tags=["Presence"])
class VenueListView(ListAPIView):
    """GET: returns enabled building definitions, accessible before opt-in."""

    permission_classes = [IsAuthenticated]
    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(enabled=True).prefetch_related("fitness_rooms")


@extend_schema(tags=["Presence"])
class OptInView(APIView):
    """GET: reads consent and privacy information. POST: updates only your consent."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ConsentSerializer)
    def get(self, request):
        return Response(ConsentSerializer(get_consent(request.user)).data)

    @extend_schema(
        request=OptInSerializer,
        responses=ConsentSerializer,
        description="Enabling requires the current policy version; withdrawal does not.",
        examples=[
            OpenApiExample(
                "Opt in",
                value={"opted_in": True, "policy_version": "presence-v1"},
                request_only=True,
            ),
            OpenApiExample("Withdraw consent", value={"opted_in": False}, request_only=True),
        ],
    )
    def post(self, request):
        serializer = OptInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opt_in = PresenceOptIn.set_for_user(request.user, **serializer.validated_data)
        return Response(ConsentSerializer(opt_in).data)


@extend_schema(tags=["Presence"])
class TokenView(APIView):
    """POST: issues or rotates a temporary token for an opted-in account."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TokenSerializer, responses={200: TokenResponseSerializer, 403: None, 429: None}
    )
    def post(self, request):
        if not PresenceOptIn.is_opted_in(request.user):
            return Response(
                {"detail": "Presence opt-in required for the current policy."}, status=403
            )
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not store.allow_issuance(request.user.pk):
            return Response({"detail": "Token issuance limit reached."}, status=429)
        token = store.issue_token(previous=serializer.validated_data.get("previous"))
        if token is None:
            return Response({"detail": "Invalid or expired previous token."}, status=403)
        return Response({"token": token, "expires_in": store.TOKEN_TTL_SECONDS})


@extend_schema(tags=["Presence"])
class HeartbeatView(APIView):
    """POST: accepts token-only presence updates and scores them by server receive time."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=HeartbeatSerializer,
        responses={204: None, 400: None, 403: None, 429: None},
        examples=[
            OpenApiExample(
                "Presence heartbeat",
                value={
                    "venue_id": "pottruck",
                    "token": "temporary-token",
                    "timestamp": "2026-10-16T17:00:00Z",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not Venue.objects.filter(pk=data["venue_id"], enabled=True).exists():
            return Response({"detail": "Unknown or disabled venue."}, status=400)
        result = store.heartbeat(data["venue_id"], data["token"])
        if result == "invalid":
            return Response({"detail": "Invalid or expired token."}, status=403)
        if result == "throttled":
            return Response({"detail": "Heartbeat too frequent."}, status=429)
        return Response(status=204)
