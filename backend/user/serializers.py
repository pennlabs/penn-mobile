from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("laundry_preferences", "fitness_preferences", "dining_preferences")


class UserSerializer(serializers.ModelSerializer):

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
