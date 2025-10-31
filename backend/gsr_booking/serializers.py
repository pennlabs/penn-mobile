from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, GSRShareCode


User = get_user_model()


class GroupRoomBookingRequestSerializer(serializers.Serializer):
    lid = serializers.IntegerField()
    room = serializers.IntegerField()

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    is_wharton = serializers.SerializerMethodField()

    def get_is_wharton(self, obj):
        return obj["lid"] == 1


class GroupMembershipSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field="name", queryset=Group.objects.all())
    color = serializers.SlugRelatedField(slug_field="color", read_only=True, source="group")

    class Meta:
        model = GroupMembership
        fields = [
            "group",
            "type",
            "pennkey_allow",
            "notifications",
            "id",
            "color",
        ]


class GroupSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False
    )
    memberships = GroupMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["owner", "memberships", "name", "color", "id"]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request is None:
            return super().create(validated_data)

        if request.user.is_authenticated:
            validated_data["owner"] = request.user

        return super().create(validated_data)


class GroupField(serializers.RelatedField):
    def to_representation(self, value):
        return {"name": value.name, "id": value.id, "color": value.color}

    def to_internal_value(self, data):
        # TODO: If you want to update based on BookingField, implement this.
        return None


class GSRSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSR
        exclude = ["in_use"]


class GSRBookingSerializer(serializers.ModelSerializer):

    gsr = GSRSerializer(read_only=False, required=False)

    class Meta:
        model = GSRBooking
        fields = ("booking_id", "gsr", "room_id", "room_name", "start", "end")


class GSRShareCodeSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()

    class Meta:
        model = GSRShareCode
        fields = ["code", "created_at", "expires_at", "status"]
        read_only_fields = fields

    def get_status(self, obj):
        if obj.booking.end and obj.booking.end <= timezone.now():
            return "expired"
        return "active"

    def get_expires_at(self, obj):
        return obj.booking.end


class SharedGSRBookingSerializer(serializers.ModelSerializer):
    """For shared bookings, does not contain any owner information."""

    building = serializers.CharField(source="gsr.name")

    class Meta:
        model = GSRBooking
        fields = ["room_name", "building", "start", "end"]
        read_only_fields = fields
