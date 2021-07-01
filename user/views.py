from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView


from user.serializers import UserSerializer
from user.models import NotificationSetting, NotificationToken


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
    '''Allows users to adjust notification settings for certain items'''

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
            notification_setting = NotificationSetting.objects.filter(user=request.user, setting=setting).first()
            if notification_setting:
                notification_setting.enabled = enabled
                notification_setting.save()
            else:
                # only creates new object if there was not previous setting
                NotificationSetting.objects.create(user=request.user, setting=setting, enabled=enabled)

        return Response({"detail": "success"})


class RegisterNotificationToken(APIView):
    '''Registers Notification Token for User (Android and/or iOS)'''
    
    def post(self, request):
        dev = True if request.data['dev'] == True else False
        if request.data['ios_token']:
            ios_token = NotificationToken.objects.filter(user=request.user, kind=NotificationToken.KIND_IOS).first()
            if ios_token:
                ios_token.token = request.data['ios_token']
                ios_token.dev = dev
                ios_token.save()
            else:
                NotificationToken.objects.create(user=request.user, kind=NotificationToken.KIND_IOS, token=request.data['ios_token'], dev=dev)
        if request.data['android_token']:
            android_token = NotificationToken.objects.filter(user=request.user, kind=NotificationToken.KIND_ANDROID).first()
            if android_token:
                android_token.token = request.data['android_token']
                android_token.dev = dev
                android_token.save()
            else:
                NotificationToken.objects.create(user=request.user, kind=NotificationToken.KIND_ANDROID, token=request.data['android_token'], dev=dev)
        return Response({"detail": "success"})



