from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import NotificationSetting, NotificationToken
from user.notifications import send_push_notification, send_push_notification_batch
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
        # style
        pk = pk.upper().replace("-", "_")

        if pk not in dict(NotificationSetting.SERVICE_OPTIONS):
            return Response({"error": "invalid service"})

        token = NotificationToken.objects.filter(user=self.request.user).first()
        if not token:
            return Response({"enabled": False})

        setting, _ = NotificationSetting.objects.get_or_create(token=token, service=pk)
        return Response({"enabled": setting.enabled})


class NotificationAlertView(APIView):
    """
    post:
    sends push notification alert if one exists
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        usernames = (
            request.data["users"] if "users" in request.data else [self.request.user.username]
        )
        service = request.data["service"]
        title = request.data["title"]
        body = request.data["body"]

        # queries tokens, filters by pennkey, service, and whether notif enabled
        tokens = NotificationToken.objects.select_related("user").filter(
            kind=NotificationToken.KIND_IOS,  # until Android implementation
            user__username__in=usernames,
            notificationsetting__service=service,
            notificationsetting__enabled=True,
        )

        if len(tokens) == 1:
            send_push_notification(tokens[0], title, body)
        elif len(tokens) > 1:
            send_push_notification_batch(tokens, title, body)

        # get users that are not being sent notifs
        failed_users = list(set(usernames) - set([token.user.username for token in tokens]))
        return Response({"success": True, "failed_users": failed_users})
