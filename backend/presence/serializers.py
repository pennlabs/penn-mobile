from rest_framework import serializers

from presence.models import Venue


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ["venue_id", "name", "geofence", "min_dwell_seconds", "exit_grace_seconds"]
