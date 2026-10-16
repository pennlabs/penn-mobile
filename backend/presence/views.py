from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from presence import store
from presence.models import PresenceOptIn, Venue
from presence.serializers import VenueSerializer


class VenueListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = VenueSerializer
    queryset = Venue.objects.filter(enabled=True)


class OptInView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"opted_in": PresenceOptIn.is_opted_in(request.user)})

    def post(self, request):
        opted_in = request.data.get("opted_in")
        if not isinstance(opted_in, bool):
            return Response({"detail": "opted_in must be a boolean."}, status=400)
        opt_in = PresenceOptIn.set_for_user(request.user, opted_in)
        return Response({"opted_in": opt_in.opted_in})


class TokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not PresenceOptIn.is_opted_in(request.user):
            return Response({"detail": "Presence opt-in required."}, status=403)
        if not store.allow_issuance(request.user.pk):
            return Response({"detail": "Token issuance limit reached."}, status=429)
        token = store.issue_token(previous=request.data.get("previous"))
        return Response({"token": token, "expires_in": store.TOKEN_TTL_SECONDS})


class HeartbeatView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        venue_id = request.data.get("venue_id")
        if not Venue.objects.filter(pk=venue_id, enabled=True).exists():
            return Response({"detail": "Unknown or disabled venue."}, status=400)
        result = store.heartbeat(venue_id, request.data.get("token"))
        if result == "invalid":
            return Response({"detail": "Invalid or expired token."}, status=403)
        if result == "throttled":
            return Response({"detail": "Heartbeat too frequent."}, status=429)
        return Response(status=204)
