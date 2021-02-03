from rest_framework import serializers

from laundry.models import LaundrySnapshot


class LaundrySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundrySnapshot
        fields = ("room", "date", "available_washers", "available_dryers", "total_washers", "total_dryers")

    def save(self):
        self.validated_data["room"] = LaundryRoom.objects.get(
            pk=self.context["views"].kwargs["room_pk"]
        )
        return super.save()


class LaundryUsageSerializer(serializers.Serializer):

    integer = serializers.IntegerField()
    laundry_snapshot = LaundrySnapshotSerializer(read_only=False, required=False)

    def save(self):
        integer = self.validated_data["integer"]

        # test





# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = ("expected_graduation", "degrees", "laundry_preferences", "dining_preferences")


# class UserSerializer(serializers.ModelSerializer):

#     profile = ProfileSerializer(read_only=False, required=False)

#     class Meta:
#         model = get_user_model()
#         fields = (
#             "id",
#             "first_name",
#             "last_name",
#             "email",
#             "username",
#             "profile",
#         )