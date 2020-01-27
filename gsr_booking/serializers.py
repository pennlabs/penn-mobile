from django.contrib.auth import get_user_model
from gsr_booking.models import Group, GroupMembership
from rest_framework import serializers


User = get_user_model()


class MiniUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
    group = serializers.SlugRelatedField(slug_field="name", queryset=Group.objects.all())
    color = serializers.SlugRelatedField(slug_field="color", read_only=True, source="group")

    class Meta:
        model = GroupMembership
        fields = ["user", "group", "type", "pennkey_allow", "notifications", "id", "color"]


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
        return None  # TODO: If you want to update based on BookingField, implement this.


class UserSerializer(serializers.ModelSerializer):
    booking_groups = GroupMembershipSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = User
        fields = ["username", "booking_groups"]
