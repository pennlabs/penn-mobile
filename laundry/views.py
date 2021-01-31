from rest_framework import generics
from rest_framework.response import Response

from laundry.models import Hall, LaundryRoom
from laundry.serializers import LaundryHallSerializer, LaundryRoomSerializer


class Halls(generics.ListAPIView):

    queryset = Hall.objects.all()
    serializer_class = LaundryHallSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = LaundryHallSerializer(queryset, many=True)
        return Response(serializer.data)


class HallStatus(generics.ListAPIView):


    def get_queryset(self):
        hall_id = self.kwargs['hall_id']
        return LaundryRoom.objects.filter(id=hall_id)

    def list(self, request, hall_id):
        queryset = self.get_queryset()
        serializer = LaundryRoomSerializer(queryset, many=True)
        return Response(serializer.data)


class HallUsage(generics.ListAPIView):

    def get_queryset(self):
        pass

    def list(self, request, hall_id):
        pass


