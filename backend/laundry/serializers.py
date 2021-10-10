from rest_framework import serializers

from laundry.models import LaundryRoom


class LaundryRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundryRoom
        fields = ("name", "hall_id", "location")
