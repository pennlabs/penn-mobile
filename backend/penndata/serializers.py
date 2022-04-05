from rest_framework import serializers

from penndata.models import Event, FitnessRoom, FitnessSnapshot, HomePageOrder


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "event_type",
            "name",
            "description",
            "image_url",
            "start_time",
            "end_time",
            "email",
            "website",
            "facebook",
        )


class HomePageOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePageOrder
        fields = ("cell", "rank")


class FitnessRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessRoom
        fields = ("name",)


class FitnessSnapshotSerializer(serializers.ModelSerializer):

    room = FitnessRoomSerializer()

    class Meta:
        model = FitnessSnapshot
        fields = ("room", "date", "count")
