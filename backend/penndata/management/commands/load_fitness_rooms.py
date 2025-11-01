from django.core.management.base import BaseCommand

from penndata.models import FitnessRoom


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        fitness_rooms = [
            "Climbing Wall",
            "Rec Lounge",
            "1st Floor Fitness",
            "Court 1",
            "Court 2",
            "Court 3",
            "Multipurpose Room",
            "2nd Floor Weight Room",
            "3rd Floor Fitness Room",
            "4th Floor Fitness Room",
            "Studio 409",
            "Sheerr Pool",
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
