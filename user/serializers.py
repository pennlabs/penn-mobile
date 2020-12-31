from rest_framework import serializers

from user.models import DiningPreference, LaundryPreference, NotificationToken, Profile


class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationToken
        fields = ("kind", "dev", "token")


class LaundryPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundryPreference
        fields = ("room_id",)


class DiningPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningPreference
        fields = ("venue_id",)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("laundry_preferences", "dining_preferences")
