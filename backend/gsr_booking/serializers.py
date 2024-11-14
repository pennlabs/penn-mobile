from typing import Any, TypeAlias

from django.contrib.auth import get_user_model
from rest_framework import serializers

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking


ValidatedData: TypeAlias = dict[str, Any]
User = get_user_model()


class GroupRoomBookingRequestSerializer(serializers.Serializer):
    lid = serializers.IntegerField()
    room = serializers.IntegerField()

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    is_wharton = serializers.SerializerMethodField()

    def get_is_wharton(self, obj: ValidatedData) -> bool:
        return obj["lid"] == 1


class GroupMembershipSerializer(serializers.ModelSerializer):
    group: serializers.SlugRelatedField = serializers.SlugRelatedField(
        slug_field="name", queryset=Group.objects.all()
    )
    color: serializers.SlugRelatedField = serializers.SlugRelatedField(
        slug_field="color", read_only=True, source="group"
    )

    class Meta:
        model = GroupMembership
        fields = ["group", "type", "pennkey_allow", "notifications", "id", "color"]


class GroupSerializer(serializers.ModelSerializer):
    owner: serializers.SlugRelatedField = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=False
    )
    memberships = GroupMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["owner", "memberships", "name", "color", "id"]

    def create(self, validated_data: ValidatedData) -> Group:
        request = self.context.get("request", None)
        if request is None:
            return super().create(validated_data)

        if request.user.is_authenticated:
            validated_data["owner"] = request.user

        return super().create(validated_data)


class GroupField(serializers.RelatedField):
    def to_representation(self, value: Group) -> dict[str, Any]:
        return {"name": value.name, "id": value.id, "color": value.color}

    def to_internal_value(self, data: ValidatedData) -> None:
        return None  # TODO: If you want to update based on BookingField, implement this.


class GSRSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSR
        exclude = ["in_use"]


class GSRBookingSerializer(serializers.ModelSerializer):

    gsr = GSRSerializer(read_only=False, required=False)

    class Meta:
        model = GSRBooking
        fields = ("booking_id", "gsr", "room_id", "room_name", "start", "end")
