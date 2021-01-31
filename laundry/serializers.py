from rest_framework import serializers

from laundry.models import Hall, LaundryRoom, LaundrySnapshot


class LaundryRoomSerializer(serializers.Serialization):
    class Meta:
        model = LaundryRoom
        fields = (
            "name",
            "hall",
            "total_washers" "total_dryers",
        )


class LaundrySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaundrySnapshot
        fields = ("date", "washers_available", "dryers_available")

    def save(self):
        self.validated_data["room"] = LaundryRoom.objects.get(
            pk=self.context["views"].kwargs["room_pk"]
        )
        return super.save()


class LaundryHallSerializer(serializers.Serialization):
    class Meta:
        model = Hall
        fields = ("name",)
