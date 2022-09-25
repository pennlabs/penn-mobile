from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import NotificationSetting, NotificationToken, Profile


class NotificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationToken
        fields = ("kind", "dev", "token")

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        token = NotificationToken.objects.filter(user=validated_data["user"]).first()

        if token:
            token.kind = validated_data["kind"]
            token.token = validated_data["token"]
            token.dev = validated_data["dev"]
            token.save()
            return token
        else:
            return super().create(validated_data)


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ("service", "enabled")

    def create(self, validated_data):
        validated_data["token"] = NotificationToken.objects.get(user=self.context["request"].user)
        setting = NotificationSetting.objects.filter(
            token=validated_data["token"], service=validated_data["service"]
        ).first()

        if setting:
            # if setting already exists, just update it
            setting.enabled = validated_data["enabled"]
            setting.save()
            return setting
        else:
            return super().create(validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
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
