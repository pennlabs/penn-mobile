from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from gsr_booking.models import (
    GSR,
    Group,
    GroupMembership,
    GSRBooking,
    GSRBookingShare,
    GSRShareCode,
    Reservation,
)


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
    booking_id = serializers.SlugRelatedField(
        slug_field="booking_id",
        source="booking",
        queryset=GSRBooking.objects.all(),
        write_only=True,
    )

    class Meta:
        model = GSRShareCode
        fields = ["code", "created_at", "expires_at", "status", "booking_id"]
        read_only_fields = ["code", "created_at", "expires_at", "status"]

    def get_status(self, obj):
        if obj.booking.end and obj.booking.end <= timezone.now():
            return "expired"
        return "active"

    def get_expires_at(self, obj):
        return obj.booking.end

    def create(self, validated_data):
        booking = validated_data["booking"]

        # Check if share code already exists for this booking
        try:
            existing_code = booking.share_code
            if existing_code.is_valid():
                return existing_code
            # Delete invalid code
            existing_code.delete()
        except GSRShareCode.DoesNotExist:
            # No existing share code so create a new one
            pass

        # Create new share code
        validated_data["owner"] = self.context["request"].user
        validated_data["code"] = GSRShareCode.generate_code()
        return super().create(validated_data)


class SharedGSRBookingSerializer(serializers.ModelSerializer):

    is_valid = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    gsr = GSRSerializer(read_only=True)

    class Meta:
        model = GSRBooking
        fields = [
            "booking_id",
            "gsr",
            "room_id",
            "room_name",
            "start",
            "end",
            "is_valid",
            "owner_name",
        ]
        read_only_fields = fields

    def get_owner_name(self, obj):
        user = obj.reservation.creator if obj.reservation else obj.user
        if not user:
            return "Unknown"

        full_name = f"{user.first_name} {user.last_name}".strip()
        if full_name:
            return full_name

        return user.username

    def get_is_valid(self, obj):
        return obj.end and obj.end > timezone.now()


class SharedReservationBookingSerializer(serializers.ModelSerializer):
    location = serializers.CharField(source="gsr.name", read_only=True)

    class Meta:
        model = GSRBooking
        fields = ["location", "room_name", "start", "end"]


class GSRBookingShareSerializer(serializers.ModelSerializer):
    reservation = serializers.PrimaryKeyRelatedField(
        queryset=Reservation.objects.all(), write_only=True, required=True
    )
    recipient = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.filter(is_active=True)
    )
    reservation_id = serializers.IntegerField(read_only=True)
    inviter = serializers.SlugRelatedField(slug_field="username", read_only=True)
    invited_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    responded_at = serializers.DateTimeField(read_only=True)
    revoked_at = serializers.DateTimeField(read_only=True)
    bookings = serializers.SerializerMethodField()

    class Meta:
        model = GSRBookingShare
        validators = []
        fields = [
            "id",
            "reservation",
            "reservation_id",
            "recipient",
            "inviter",
            "status",
            "invited_at",
            "created_at",
            "updated_at",
            "responded_at",
            "revoked_at",
            "bookings",
        ]
        read_only_fields = [
            "id",
            "reservation_id",
            "inviter",
            "status",
            "invited_at",
            "created_at",
            "updated_at",
            "responded_at",
            "revoked_at",
            "bookings",
        ]

    def validate(self, attrs):
        request = self.context["request"]
        reservation = attrs["reservation"]
        recipient = attrs["recipient"]

        if reservation.creator_id != request.user.id:
            raise serializers.ValidationError(
                {"reservation": "Only the reservation owner can invite others."}
            )
        if recipient.id == request.user.id:
            raise serializers.ValidationError({"recipient": "You cannot invite yourself."})
        if reservation.is_cancelled or reservation.end <= timezone.now():
            raise serializers.ValidationError(
                {"reservation": "Only active, upcoming reservations can be shared."}
            )
        if not reservation.gsrbooking_set.filter(
            is_cancelled=False, end__gt=timezone.now()
        ).exists():
            raise serializers.ValidationError(
                {"reservation": "This reservation has no active bookings to share."}
            )
        return attrs

    def create(self, validated_data):
        reservation = validated_data.pop("reservation")
        recipient = validated_data["recipient"]
        inviter = self.context["request"].user

        share, created = GSRBookingShare.objects.get_or_create(
            reservation=reservation,
            recipient=recipient,
            defaults={"inviter": inviter},
        )
        if not created and share.status in (GSRBookingShare.DECLINED, GSRBookingShare.REVOKED):
            share.inviter = inviter
            share.status = GSRBookingShare.PENDING
            share.invited_at = timezone.now()
            share.responded_at = None
            share.revoked_at = None
            share.save(
                update_fields=[
                    "inviter",
                    "status",
                    "invited_at",
                    "responded_at",
                    "revoked_at",
                    "updated_at",
                ]
            )
        return share

    def get_bookings(self, obj):
        request = self.context.get("request")
        can_view = (
            request
            and (
                obj.inviter_id == request.user.id
                or (obj.recipient_id == request.user.id and obj.status == GSRBookingShare.ACCEPTED)
            )
            and obj.is_relevant()
        )
        if not can_view:
            return []

        bookings = obj.reservation.gsrbooking_set.filter(
            is_cancelled=False, end__gt=timezone.now()
        ).select_related("gsr")
        return SharedReservationBookingSerializer(bookings, many=True).data
