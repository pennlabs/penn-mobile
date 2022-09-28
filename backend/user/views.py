from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import NotificationSetting, NotificationToken
from user.notifications import (
    send_delayed_push_notif,
    send_delayed_push_notif_batch,
    send_push_notif,
    send_push_notif_batch,
)
from user.serializers import (
    NotificationSettingSerializer,
    NotificationTokenSerializer,
    UserSerializer,
)


class UserView(generics.RetrieveUpdateAPIView):
    """
    get:
    Return information about the logged in user.

    update:
    Update information about the logged in user.
    You must specify all of the fields or use a patch request.

    patch:
    Update information about the logged in user.
    Only updates fields that are passed to the server.
    """

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class NotificationTokenView(viewsets.ModelViewSet):
    """
    get:
    Return notification tokens of user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationTokenSerializer

    def get_queryset(self):
        return NotificationToken.objects.filter(user=self.request.user)


class NotificationSettingView(viewsets.ModelViewSet):
    """
    get:
    Return notification settings of user.

    post:
    Creates/updates new notification setting of user for a specific service.

    check:
    Checks if user wants notification for specified serice.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSettingSerializer

    def get_queryset(self):
        return NotificationSetting.objects.filter(token__user=self.request.user)

    @action(detail=True, methods=["get"])
    def check(self, request, pk=None):
        """
        Returns whether the user wants notification for specified service.
        :param pk: service name
        """
        if pk not in dict(NotificationSetting.SERVICE_OPTIONS):
            return Response({"detail": "Invalid service."}, status=status.HTTP_400_BAD_REQUEST)

        token = NotificationToken.objects.filter(user=self.request.user).exclude(token="").first()
        if not token:
            # assumes that if token is missing, enabled should be returned as 'False'
            return Response({"enabled": False, "missing_token": True})

        setting, _ = NotificationSetting.objects.get_or_create(token=token, service=pk)
        return Response({"enabled": setting.enabled, "missing_token": False})


class NotificationAlertView(APIView):
    """
    post:
    sends push notification alert if one exists
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        usernames = request.data.get("users", [self.request.user.username])
        service = request.data.get("service", None)
        title = request.data.get("title", None)
        body = request.data.get("body", None)
        delay = request.data.get("delay", None)

        if None in [service, title, body]:
            return Response(
                {"detail": "Missing required parameters."}, status=status.HTTP_400_BAD_REQUEST
            )
        if service not in dict(NotificationSetting.SERVICE_OPTIONS):
            return Response({"detail": "Invalid service."}, status=status.HTTP_400_BAD_REQUEST)

        # queries tokens, filters by pennkey, service, and whether notif enabled
        tokens = (
            NotificationToken.objects.select_related("user")
            .filter(
                kind=NotificationToken.KIND_IOS,  # NOTE: until Android implementation
                user__username__in=usernames,
                notificationsetting__service=service,
                notificationsetting__enabled=True,
            )
            .exclude(token="")
            .values_list("user__username", "token", "dev")
        )

        # unpack list of tuples
        if tokens:
            success_users, tokens, devs = zip(*tokens)
        else:
            success_users, devs = list(), list()
        failed_users = list(set(usernames) - set(success_users))

        if len(tokens) == 1:
            if delay:
                send_delayed_push_notif(tokens[0], title, body, delay, devs[0])
            else:
                send_push_notif(tokens[0], title, body, devs[0])
        elif len(tokens) > 1:
            # ensure that tokens are the same type
            if any(dev != devs[0] for dev in devs):
                return Response(
                    {"detail": "Includes both non-dev and dev users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if delay:
                send_delayed_push_notif_batch(tokens, title, body, devs[0])
            else:
                send_push_notif_batch(tokens, title, body, devs[0])

        return Response({"success_users": success_users, "failed_users": failed_users})
