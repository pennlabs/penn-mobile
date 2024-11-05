from typing import Any, TypeAlias

from rest_framework import serializers

from penndata.models import (
    AnalyticsEvent,
    CalendarEvent,
    Event,
    FitnessRoom,
    FitnessSnapshot,
    HomePageOrder,
)


ValidatedData: TypeAlias = dict[str, Any]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = (
            "event_type",
            "name",
            "description",
            "location",
            "image_url",
            "start",
            "end",
            "email",
            "website",
        )


class CalendarEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarEvent
        fields = ("event", "date")


class HomePageOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomePageOrder
        fields = ("cell", "rank")


class FitnessRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessRoom
        fields = "__all__"


class FitnessSnapshotSerializer(serializers.ModelSerializer):

    room = FitnessRoomSerializer()

    class Meta:
        model = FitnessSnapshot
        fields = ("room", "date", "count", "capacity")


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ("created_at", "cell_type", "index", "post", "poll", "is_interaction")

    def create(self, validated_data: ValidatedData) -> AnalyticsEvent:
        validated_data["user"] = self.context["request"].user
        if validated_data["poll"] and validated_data["post"]:
            raise serializers.ValidationError(
                detail={"detail": "Poll and Post interactions are mutually exclusive."}
            )
        return super().create(validated_data)
