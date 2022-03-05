from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import NotificationToken, Profile


class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationToken
        fields = ("kind", "dev", "token")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        tokens = NotificationToken.objects.filter(user=validated_data["user"]).first()
        if tokens:
            # if token already exists, just update it
            tokens.kind = validated_data["kind"]
            tokens.token = validated_data["token"]
            tokens.save()
            return tokens
        else:
            return super().create(validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        # removed "expected_graduation" and "degrees"
        fields = ("laundry_preferences", "dining_preferences")


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
