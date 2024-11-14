from typing import Any

from django.core.management.base import BaseCommand

from penndata.models import FitnessRoom


class Command(BaseCommand):
    def handle(self, *args: Any, **kwargs: Any) -> None:
        fitness_rooms = [
            "4th Floor Fitness",
            "3rd Floor Fitness",
            "2nd Floor Strength",
            "Basketball Courts",
            "MPR",
            "Climbing Wall",
            "1st Floor Fitness",
            "Pool-Shallow",
            "Pool-Deep",
        ]
        for room in fitness_rooms:
            obj, _ = FitnessRoom.objects.get_or_create(name=room)
            if obj.image_url == "":
                s3_image_name = (
                    room.replace(" ", "_") + (".png" if "2nd" in room else ".jpg")
                    if "Pool" not in room
                    else "Pool.jpeg"
                )
                obj.image_url = (
                    f"https://s3.us-east-2.amazonaws.com/penn.mobile/pottruck/{s3_image_name}"
                )
                obj.save()

        self.stdout.write("Uploaded Fitness Rooms!")
