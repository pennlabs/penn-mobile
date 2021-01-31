from rest_framework import serializers

from laundry.models import Hall, LaundryRoom, LaundrySnapshot


class LaundrySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundrySnapshot
        fields = ("date", "washers_available", "dryers_available")

    def save(self):
        self.validated_data["room"] = LaundryRoom.objects.get(
            pk=self.context["views"].kwargs["room_pk"]
        )
        return super.save()


class LaundryHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ("name", )


class LaundryRoomSerializer(serializers.ModelSerializer):

    hall = LaundryHallSerializer(read_only=False, required=True)

    class Meta:
        model = LaundryRoom
        fields = (
            "id",
            "name",
            "total_washers",
            "total_dryers",
            "hall",
        )

# class LaundryRoomStatusSerializer(serializers.ModelSerializer):

#     room = LaundryRoomSerializer(read_only=False, required=True)
#     hall = LaundryHallSerializer(read_only=False, required=True)

#     class Meta:
#         model = LaundryRoom
#         fields = ("room", "hall")
