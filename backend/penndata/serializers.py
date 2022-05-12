from rest_framework import serializers

from penndata.models import AnalyticsEvent, Event, FitnessRoom, FitnessSnapshot, HomePageOrder


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


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = ("created_at", "cell_type", "index", "post", "poll", "is_interaction")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if validated_data["poll"] and validated_data["post"]:
            raise serializers.ValidationError(
                detail={"detail": "Poll and Post interactions are mutually exclusive."}
            )
        return super().create(validated_data)
