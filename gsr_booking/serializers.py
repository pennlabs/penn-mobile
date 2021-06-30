from django.contrib.auth import get_user_model
from rest_framework import serializers

from gsr_booking.api_wrapper import LibCalWrapper
from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, GSRBookingCredentials
from user.serializers import ProfileSerializer


User = get_user_model()


class GroupRoomBookingRequestSerializer(serializers.Serializer):
    lid = serializers.IntegerField()
    room = serializers.IntegerField()

    start = serializers.DateTimeField()
    end = serializers.DateTimeField()

    is_wharton = serializers.SerializerMethodField()

    def get_is_wharton(self, obj):
        return obj["lid"] == 1


class GroupBookingRequestSerializer(serializers.Serializer):
    room_bookings = GroupRoomBookingRequestSerializer(many=True)


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
        fields = [
            "user",
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
        return None  # TODO: If you want to update based on BookingField, implement this.


class GSRBookingCredentialsSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all(), required=True
    )

    class Meta:
        model = GSRBookingCredentials
        fields = ["user", "session_id", "expiration_date", "date_updated"]


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


class GSRSerializer(serializers.ModelSerializer):
    class Meta:
        model = GSR
        fields = "__all__"


class GSRBookingSerializer(serializers.ModelSerializer):

    room = GSRSerializer
    profile = ProfileSerializer

    class Meta:
        model = GSRBooking
        fields = "__all__"

    def create(self, validated_data):
        instance = super().create(validated_data)

        # TODO: do the wharton scheduling here

        data = self.get_data(validated_data)
        LCW = LibCalWrapper()

        # does the room booking on LibCal API
        response = LCW.book_room(
            validated_data["room"].rid, validated_data["start"], validated_data["end"], *data
        )
        if response["error"] is not None:
            # deletes object if there is an error
            instance.delete()
            raise serializers.ValidationError({"detail": response["error"]})
        else:
            instance.booking_id = response["booking_id"]
            instance.save()
        return instance

    def get_data(self, validated_data):
        user = validated_data["profile"].user
        custom = {
            "q3699": self.get_affiliation(user.email),
            "q2533": validated_data["profile"].phone_number,
            "q2555": validated_data["size"],
            "q2537": validated_data["size"],
        }
        # returns data in usable format
        context = [user.first_name, user.last_name, user.email, validated_data["name"], custom]
        return context

    def get_affiliation(self, email):
        if "wharton" in email:
            return "Wharton"
        elif "seas" in email:
            return "SEAS"
        elif "sas" in email:
            return "SAS"
        else:
            return "Other"
