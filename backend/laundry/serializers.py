from rest_framework import serializers

from laundry.models import LaundryRoom


class LaundryRoomSerializer(serializers.ModelSerializer):
    # tech debt but we're rewriting at some point and this maintains frontend-compatibility
    hall_id = serializers.IntegerField(source="room_id")

    class Meta:
        model = LaundryRoom
        fields = ("name", "hall_id", "location")
