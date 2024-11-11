from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import Profile

# class NotificationSettingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NotificationSetting
#         fields = ("id", "service", "enabled")

#     def create(self, validated_data):
#         validated_data["token"] = NotificationToken.objects.get(user=self.context["request"].user)
#         setting = NotificationSetting.objects.filter(
#             token=validated_data["token"], service=validated_data["service"]
#         ).first()
#         if setting:
#             raise serializers.ValidationError(detail={"detail": "Setting already created."})
#         return super().create(validated_data)

#     def update(self, instance, validated_data):
#         if instance.service != validated_data["service"]:
#             raise serializers.ValidationError(detail={"detail": "Cannot change setting service."})
#         return super().update(instance, validated_data)


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
