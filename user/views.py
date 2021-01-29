from .models import Profile, Degree
from .serializers import PrivateUserSerializer

from rest_framework import generics



class UserView(generics.RetrieveUpdateAPIView):
    '''
    get:
    Return information about the logged in user.

    update:
    Update information about the logged in user.
    You must specify all of the fields or use a patch request.

    patch:
    Update information about the logged in user.
    Only updates fields that are passed to the server.
    '''

    serializer_class = PrivateUserSerializer


    def get_object(self):
        return self.request.user
