from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from rest_framework import viewsets
from rest_framework.decorators import action
from apns2.client import APNsClient
from apns2.credentials import TokenCredentials
from apns2.payload import Payload

import os


from user.models import NotificationSetting, NotificationToken
from user.serializers import UserSerializer, NotificationTokenSerializer

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


class NotificationSettingsView(APIView):
    """Allows users to adjust notification settings for certain items"""

    def get(self, request):
        response = {}
        settings = NotificationSetting.objects.filter(user=request.user)

        # returns dictionary of items and whether or not notifications are enabled
        for setting in settings:
            response[setting.setting] = setting.enabled
        return Response({"settings": response})

    def post(self, request):
        for setting in request.data:
            enabled = request.data[setting]
            # filters if there was a previous notification setting for that item
            notification_setting = NotificationSetting.objects.filter(
                user=request.user, setting=setting
            ).first()
            if notification_setting:
                notification_setting.enabled = enabled
                notification_setting.save()
            else:
                # only creates new object if there was not previous setting
                NotificationSetting.objects.create(
                    user=request.user, setting=setting, enabled=enabled
                )

        return Response({"detail": "success"})


class RegisterNotificationToken(APIView):
    """Registers Notification Token for User (Android and/or iOS)"""

    def post(self, request):
        dev = request.data["dev"]
        if request.data["ios_token"]:
            ios_token = NotificationToken.objects.filter(
                user=request.user, kind=NotificationToken.KIND_IOS
            ).first()
            if ios_token:
                ios_token.token = request.data["ios_token"]
                ios_token.dev = dev
                ios_token.save()
            else:
                NotificationToken.objects.create(
                    user=request.user,
                    kind=NotificationToken.KIND_IOS,
                    token=request.data["ios_token"],
                    dev=dev,
                )
        if request.data["android_token"]:
            android_token = NotificationToken.objects.filter(
                user=request.user, kind=NotificationToken.KIND_ANDROID
            ).first()
            if android_token:
                android_token.token = request.data["android_token"]
                android_token.dev = dev
                android_token.save()
            else:
                NotificationToken.objects.create(
                    user=request.user,
                    kind=NotificationToken.KIND_ANDROID,
                    token=request.data["android_token"],
                    dev=dev,
                )
        return Response({"detail": "success"})


class SendNotification(viewsets.ViewSet):

    queryset = NotificationToken.objects.all()
    serializer_class = NotificationTokenSerializer

    @action(detail=False, methods=["post"])
    def send(self, request):
        obj = get_object_or_404(NotificationToken, user=request.user, kind=NotificationToken.KIND_IOS)
        self.send_push_notification(obj.token, request.data['title'], request.data['body'], obj.dev)
        return Response({"detail": "success"})

    @action(detail=False, methods=["post"])
    def send_internal(self, request):
        user = get_object_or_404(User, username=request.user.username)
        obj = get_object_or_404(NotificationToken, user=user, kind=NotificationToken.KIND_IOS)
        self.send_push_notification(obj.token, request.data['title'], request.data['body'], obj.dev)
        return Response({"detail": "success"})
    
    @action(detail=False, methods=["post"])
    def send_token_internal(self, request):
        self.send_push_notification(request.data['token'], request.data['title'], request.data['body'], True)
        return Response({"detail": "success"})

    def get_client(self, isDev):
        auth_key_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ios_key.p8"
        )
        auth_key_id = "443RV92X4F"
        team_id = "VU59R57FGM"
        token_credentials = TokenCredentials(
            auth_key_path=auth_key_path, auth_key_id=auth_key_id, team_id=team_id
        )
        client = APNsClient(credentials=token_credentials, use_sandbox=isDev)
        return client

    def send_push_notification(self, token, title, body, isDev=False):
        client = self.get_client(isDev)
        alert = {"title": title, "body": body}
        payload = Payload(alert=alert, sound="default", badge=0)
        topic = "org.pennlabs.PennMobile"
        client.send_notification(token, payload, topic)


    def send_push_notification_batch(self, notifications, isDev=False):
        client = self.get_client(isDev)
        topic = "org.pennlabs.PennMobile"
        client.send_notification_batch(notifications=notifications, topic=topic)

