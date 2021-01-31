from django.db import models


class Hall(models.Model):
    name = models.CharField(max_length=25)


class LaundryRoom(models.Model):
    name = models.TextField()
    total_washers = models.IntegerField(default=0, null=False)
    total_dryers = models.IntegerField(default=0, null=False)
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE, related_name="halls")


class LaundrySnapshot(models.Model):
    room = models.ForeignKey(LaundryRoom, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now=True)
    washers_available = models.IntegerField()
    dryers_available = models.IntegerField()
