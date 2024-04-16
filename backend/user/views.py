from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from identity.permissions import B2BPermission
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import NotificationSetting, NotificationToken
from user.notifications import send_push_notifications
from user.serializers import (
    NotificationSettingSerializer,
    NotificationTokenSerializer,
    UserSerializer,
)


User = get_user_model()


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

    permission_classes = [B2BPermission("urn:pennlabs:*") | IsAuthenticated]
    serializer_class = NotificationSettingSerializer

    def is_authorized(self, request):
        return request.user and request.user.is_authenticated

    def get_queryset(self):
        if self.is_authorized(self.request):
            return NotificationSetting.objects.filter(token__user=self.request.user)
        return NotificationSetting.objects.none()

    @action(detail=True, methods=["get"])
    def check(self, request, pk=None):
        """
        Returns whether the user wants notification for specified service.
        :param pk: service name
        """

        if pk not in dict(NotificationSetting.SERVICE_OPTIONS):
            return Response({"detail": "Invalid Parameters."}, status=400)

        pennkey = request.GET.get("pennkey")
        user = (
            request.user
            if self.is_authorized(request)
            else get_object_or_404(User, username=pennkey)
        )

        token = NotificationToken.objects.filter(user=user).first()
        if not token:
            return Response({"service": pk, "enabled": False})
        setting, _ = NotificationSetting.objects.get_or_create(token=token, service=pk)
        return Response(NotificationSettingSerializer(setting).data)


class NotificationAlertView(APIView):
    """
    post:
    sends push notification alert if one exists
    """

    permission_classes = [B2BPermission("urn:pennlabs:*") | IsAuthenticated]

    def post(self, request):
        users = (
            [self.request.user.username]
            if request.user and request.user.is_authenticated
            else request.data.get("users", list())
        )
        service = request.data.get("service")
        title = request.data.get("title")
        body = request.data.get("body")
        delay = max(request.data.get("delay", 0), 0)
        is_dev = request.data.get("is_dev", False)

        if None in [service, title, body]:
            return Response({"detail": "Missing required parameters."}, status=400)
        if service not in dict(NotificationSetting.SERVICE_OPTIONS):
            return Response({"detail": "Invalid service."}, status=400)

        success_users, failed_users = send_push_notifications(
            users, service, title, body, delay, is_dev
        )

        return Response({"success_users": success_users, "failed_users": failed_users})


class ClearCookiesView(APIView):
    """
    post:
    Clears all cookies from the browser
    """

    def get(self, request):
        next_url = request.GET.get("next", None)
        response = (
            HttpResponseRedirect(f"/api/accounts/login/?next={next_url}")
            if next_url
            else Response({"detail": "Cookies Cleared"})
        )
        response.delete_cookie("sessionid")
        response.delete_cookie("csrftoken")
        return response
