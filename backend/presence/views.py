from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from presence import blind, store
from presence.consent import get_consent
from presence.models import PresenceOptIn, Venue
from presence.serializers import (
    ConsentSerializer,
    HeartbeatSerializer,
    OptInSerializer,
    TokenKeySerializer,
    TokenResponseSerializer,
    TokenSerializer,
    VenueSerializer,
)


@extend_schema(tags=["Presence"])
class VenueListView(ListAPIView):
    """GET: returns enabled building definitions, accessible before opt-in."""

    permission_classes = [IsAuthenticated]
    serializer_class = VenueSerializer
    queryset = (
        Venue.objects.filter(enabled=True)
        .select_related("dining_venue")
        .prefetch_related("fitness_rooms")
    )


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
class TokenKeyView(APIView):
    """GET: the public key clients blind their tokens against. It changes every hour."""

    authentication_classes = []
    permission_classes = []

    @extend_schema(responses=TokenKeySerializer)
    def get(self, request):
        return Response(blind.key_info())


@extend_schema(tags=["Presence"])
class TokenView(APIView):
    """POST: blind-signs a token made on the device, for an opted-in account.

    The server sees who is asking but not the token, so it cannot later tell which
    heartbeats belong to this account.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=TokenSerializer,
        responses={200: TokenResponseSerializer, 400: None, 403: None, 409: None, 429: None},
    )
    def post(self, request):
        if not PresenceOptIn.is_opted_in(request.user):
            return Response(
                {"detail": "Presence opt-in required for the current policy."}, status=403
            )
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key_id = serializer.validated_data["key_id"]
        if key_id != blind.current_key_id():
            return Response(
                {"detail": "Signing key has rotated; blind again.", "key": blind.key_info()},
                status=409,
            )
        if not store.allow_issuance(request.user.pk):
            return Response({"detail": "Token issuance limit reached."}, status=429)
        try:
            message = blind.decode(serializer.validated_data["blinded_message"])
            blind_signature = blind.blind_sign(key_id, message)
        except blind.StaleKey:
            return Response(
                {"detail": "Signing key has rotated; blind again.", "key": blind.key_info()},
                status=409,
            )
        except ValueError:
            return Response({"blinded_message": ["Not a valid blinded message."]}, status=400)
        return Response(
            {
                "key_id": key_id,
                "blind_signature": blind.encode(blind_signature),
                "expires_in": blind.expires_in(key_id),
            }
        )


@extend_schema(tags=["Presence"])
class HeartbeatView(APIView):
    """POST: accepts signed-token presence updates and scores them by server receive time."""

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
                    "token": "token-made-on-the-device",
                    "key_id": "498765",
                    "signature": "base64-unblinded-signature",
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
        if not blind.verify(data["key_id"], data["token"], data["signature"]):
            return Response({"detail": "Invalid or expired token."}, status=403)
        result = store.heartbeat(data["venue_id"], data["token"], data.get("previous_token"))
        if result == "invalid":
            return Response({"detail": "Invalid or expired token."}, status=403)
        if result == "throttled":
            return Response({"detail": "Heartbeat too frequent."}, status=429)
        return Response(status=204)
