from abc import ABC

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseRedirect
from identity.permissions import B2BPermission
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from user.models import AndroidNotificationToken, IOSNotificationToken, NotificationService
from user.notifications import (
    android_send_notification,
    ios_send_dev_notification,
    ios_send_notification,
)
from user.serializers import UserSerializer


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


class NotificationTokenView(APIView, ABC):
    # permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.request.method == "DELETE":
            return []
        return [IsAuthenticated()]

    queryset = None

    def get_defaults(self):
        raise NotImplementedError  # pragma: no cover

    def post(self, request, token):
        _, created = self.queryset.update_or_create(token=token, defaults=self.get_defaults())
        if created:
            return Response({"detail": "Token created."}, status=201)
        return Response({"detail": "Token updated."})

    def delete(self, request, token):
        self.queryset.filter(token=token).delete()
        return Response({"detail": "Token deleted."})


class IOSNotificationTokenView(NotificationTokenView):
    queryset = IOSNotificationToken.objects.all()

    def get_defaults(self):
        is_dev = self.request.data.get("is_dev", False)
        return {"user": self.request.user, "is_dev": is_dev}


class AndroidNotificationTokenView(NotificationTokenView):
    queryset = AndroidNotificationToken.objects.all()

    def get_defaults(self):
        return {"user": self.request.user}


class NotificationServiceSettingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        services = NotificationService.objects.all().prefetch_related("enabled_users")
        return Response(
            {
                service.name: service.enabled_users.filter(id=user.id).exists()
                for service in services
            }
        )

    def put(self, request):
        user = request.user
        settings = request.data
        if not isinstance(settings, dict) or not all(
            isinstance(value, bool) for value in settings.values()
        ):
            return Response({"detail": "Invalid request"}, status=400)

        try:
            with transaction.atomic():
                user.notificationservice_set.add(
                    *[service for service, enabled in settings.items() if enabled]
                )
                user.notificationservice_set.remove(
                    *[service for service, enabled in settings.items() if not enabled]
                )
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"detail": "Settings updated."})


class NotificationServiceView(APIView):
    permission_classes = [IsAuthenticated]

    # TODO: this is becoming a common pattern, consider abstracting
    def get(self, request):
        return Response(NotificationService.objects.all().values_list("name", flat=True))


class NotificationAlertView(APIView):
    """
    post:
    sends push notification alert if one exists
    """

    permission_classes = [B2BPermission("urn:pennlabs:*") | IsAuthenticated]

    def post(self, request):
        usernames = (
            [self.request.user.username]
            if request.user and request.user.is_authenticated
            else request.data.get("users", list())
        )

        service = request.data.get("service")
        title = request.data.get("title")
        body = request.data.get("body")
        delay = max(request.data.get("delay", 0), 0)

        if None in [service, title, body]:
            return Response({"detail": "Missing required parameters."}, status=400)

        if not (service_obj := NotificationService.objects.filter(name=service).first()):
            return Response({"detail": "Invalid service."}, status=400)

        users_with_service = service_obj.enabled_users.filter(username__in=usernames)

        ios_tokens = IOSNotificationToken.objects.filter(user__in=users_with_service, is_dev=False)
        ios_dev_tokens = IOSNotificationToken.objects.filter(
            user__in=users_with_service, is_dev=True
        )
        android_tokens = AndroidNotificationToken.objects.filter(user__in=users_with_service)

        for tokens, send in [
            (ios_tokens, ios_send_notification),
            (ios_dev_tokens, ios_send_dev_notification),
            (android_tokens, android_send_notification),
        ]:
            if tokens_list := list(tokens.values_list("token", flat=True)):
                send.apply_async(args=(tokens_list, title, body), countdown=delay)

        users_with_service_usernames = users_with_service.values_list("username", flat=True)
        users_not_reached_usernames = list(set(usernames) - set(users_with_service_usernames))
        return Response(
            {
                "success_users": users_with_service_usernames,
                "failed_users": users_not_reached_usernames,
            }
        )


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
