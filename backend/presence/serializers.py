from collections import Counter
from collections.abc import Mapping

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from dining.models import Venue as DiningVenue
from penndata.models import FitnessRoom
from presence.consent import current_policy
from presence.models import PresenceOptIn, Venue


class GeofenceSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    radius_m = serializers.FloatField()


class VenueSerializer(serializers.ModelSerializer):
    scope = serializers.CharField(default="building", read_only=True)
    geofence = GeofenceSerializer(read_only=True)
    dining_venue_id = serializers.IntegerField(read_only=True, allow_null=True)
    fitness_room_ids = serializers.PrimaryKeyRelatedField(
        source="fitness_rooms", many=True, read_only=True
    )

    class Meta:
        model = Venue
        fields = [
            "venue_id",
            "name",
            "geofence",
            "min_dwell_seconds",
            "exit_grace_seconds",
            "kind",
            "scope",
            "max_accuracy_m",
            "opening_hours",
            "configuration_version",
            "dining_venue_id",
            "fitness_room_ids",
        ]


class PrivacyPolicySerializer(serializers.Serializer):
    version = serializers.CharField()
    collection_active = serializers.BooleanField()
    description = serializers.CharField()
    token_ttl_seconds = serializers.IntegerField()
    active_window_seconds = serializers.IntegerField()


class ConsentSerializer(serializers.ModelSerializer):
    opted_in = serializers.BooleanField(source="has_current_consent", read_only=True)
    updated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    policy = serializers.SerializerMethodField()

    class Meta:
        model = PresenceOptIn
        fields = ["opted_in", "policy_version", "consented_at", "updated_at", "revision", "policy"]

    @extend_schema_field(PrivacyPolicySerializer)
    def get_policy(self, obj):
        return current_policy()


class OptInSerializer(serializers.Serializer):
    opted_in = serializers.BooleanField()
    policy_version = serializers.CharField(max_length=64, required=False, allow_blank=True)

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            if set(data) - set(self.fields):
                raise serializers.ValidationError({"non_field_errors": ["Unknown consent fields."]})
            if "opted_in" in data and not isinstance(data["opted_in"], bool):
                raise serializers.ValidationError({"opted_in": "Must be a boolean."})
        return super().to_internal_value(data)


class TokenSerializer(serializers.Serializer):
    previous = serializers.CharField(max_length=128, required=False)


class TokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_in = serializers.IntegerField()


class HeartbeatSerializer(serializers.Serializer):
    venue_id = serializers.SlugField(max_length=64)
    token = serializers.CharField(max_length=128)
    # Accepted for client compatibility; Redis scores always use server receive time.
    timestamp = serializers.CharField(required=False)


class VenueImportSerializer(serializers.ModelSerializer):
    dining_venue_id = serializers.PrimaryKeyRelatedField(
        source="dining_venue", queryset=DiningVenue.objects.all(), required=False, allow_null=True
    )
    fitness_room_names = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )

    class Meta:
        model = Venue
        fields = [
            "venue_id",
            "name",
            "kind",
            "enabled",
            "geofence",
            "min_dwell_seconds",
            "exit_grace_seconds",
            "max_accuracy_m",
            "opening_hours",
            "capacity",
            "min_sample_size",
            "calibration",
            "dining_venue_id",
            "fitness_room_names",
        ]

    def to_internal_value(self, data):
        if isinstance(data, Mapping) and set(data) - set(self.fields):
            raise serializers.ValidationError({"non_field_errors": ["Unknown venue fields."]})
        return super().to_internal_value(data)

    def validate_fitness_room_names(self, names):
        if len(names) != len(set(names)):
            raise serializers.ValidationError("Fitness room names must be unique.")
        rooms = list(FitnessRoom.objects.filter(name__in=names))
        matches = Counter(room.name for room in rooms)
        for name in names:
            if matches[name] != 1:
                raise serializers.ValidationError(
                    f"Fitness room '{name}' must match exactly one existing room."
                )
        return rooms

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if attrs.get("fitness_room_names") and kind != Venue.Kind.GYM:
            raise serializers.ValidationError({"fitness_room_names": "Only gyms can link rooms."})
        return attrs
