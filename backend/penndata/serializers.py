from rest_framework import serializers

from penndata.models import Event, FitnessRoom, HomePageOrder


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
