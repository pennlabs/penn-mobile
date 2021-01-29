from rest_framework import serializers
from django.contrib.auth import get_user_model


from .models import NotificationToken, Profile


class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationToken
        fields = ("kind", "dev", "token")


# class LaundryPreferenceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LaundryPreference
#         fields = ("room_id",)


# class DiningPreferenceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DiningPreference
#         fields = ("venue_id",)


class ProfileSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Profile
        fields = ("laundry_preferences", "dining_preferences", "expected_graduation", "degrees")


class PrivateUserSerializer(serializers.ModelSerializer):

    profile = ProfileSerializer(read_only=False, required=False)

    class Meta:
        model = get_user_model()
        fields = (  
            "id",
            "first_name",
            "last_name",
            "email",
            "username",
            "profile",
        )

