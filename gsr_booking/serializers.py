from django.contrib.auth import get_user_model
from gsr_booking.models import Group, GroupMembership, GSRBookingCredentials
from rest_framework import serializers


User = get_user_model()


class GroupMembershipSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field="name", queryset=Group.objects.all())

    class Meta:
        model = GroupMembership
        fields = ["username", "group", "type", "pennkey_allow", "notifications"]


class GroupSerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())
    members = serializers.SlugRelatedField(many=True, slug_field="username", read_only=True)

    class Meta:
        model = Group
        fields = ["owner", "members", "name", "color", "id"]


class GroupField(serializers.RelatedField):
    def to_representation(self, value):
        return {"name": value.name, "id": value.id, "color": value.color}

    def to_internal_value(self, data):
        return None  # TODO: If you want to update based on BookingField, implement this.


class GSRBookingCredentialsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = GSRBookingCredentials
        fields = ["user", "session_id", "expiration_date", "date_added", "email"]


class UserSerializer(serializers.ModelSerializer):
    booking_groups = serializers.SerializerMethodField()

    def get_booking_groups(self, obj):
        result = []
        for membership in GroupMembership.objects.filter(accepted=True, user=obj):
            result.append(
                {
                    "name": membership.group.name,
                    "id": membership.group.id,
                    "color": membership.group.color,
                    "pennkey_allow": membership.pennkey_allow,
                    "notifications": membership.notifications,
                }
            )

        return result

    class Meta:
        model = User
        fields = ["username", "booking_groups"]
