# from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from user.models import NotificationToken
# from user.notifications import send_push_notification
from user.serializers import NotificationTokenSerializer, UserSerializer


# from rest_framework.response import Response
# from rest_framework.views import APIView


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


class NotificationView(viewsets.ModelViewSet):
    """
    get:
    Return notification tokens of user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationTokenSerializer

    def get_queryset(self):
        return NotificationToken.objects.filter(user=self.request.user)


# class SendNotification(APIView):
#     """Sends push notification alert if one exists."""

#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         title = request.data["title"]
#         body = request.data["body"]

#         # only iOS for now
#         token = get_object_or_404(
#             NotificationToken, user=self.request.user, kind=NotificationToken.KIND_IOS
#         )

#         send_push_notification(token.token, title, body)
#         return Response({"success": True})
