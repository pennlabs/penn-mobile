from rest_framework import serializers

from laundry.models import LaundrySnapshot


class LaundrySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundrySnapshot
        fields = (
            "room",
            "date",
            "available_washers",
            "available_dryers",
            "total_washers",
            "total_dryers",
        )
