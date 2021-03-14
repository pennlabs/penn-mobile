<<<<<<< HEAD
from django.db import models

from user.models import Profile

=======
# Create your models here.

# create venues
>>>>>>> d3f6306d09f285f0293e8c0148e17a34e80ff3d1

class Venue(models.Model):
    venue_id = models.IntegerField()
    image_url = models.URLField()

<<<<<<< HEAD
    def __str__(self):
        return str(self.venue_id)


class DiningPreference(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    venue_id = models.IntegerField()

    def __str__(self):
        return f"{self.profile} - {self.venue_id}"


class DiningTransaction(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField()
    description = models.TextField()
    amount = models.FloatField()
    balance = models.FloatField(default=0)

    def __str__(self):
        return f"{self.profile} - {self.date} - {self.amount}"


class DiningBalance(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    dollars = models.FloatField()
    swipes = models.IntegerField()
    guest_swipes = models.IntegerField()

    def __str__(self):
        return f"{self.profile} - {self.date}"
=======


"""
class DiningPreference(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
    user_id = sqldb.Column(sqldb.Integer, sqldb.ForeignKey("user.id"), nullable=False)
    account = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"), nullable=True)
    venue_id = sqldb.Column(sqldb.Integer, nullable=False)


class DiningBalance(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"))
    dining_dollars = sqldb.Column(sqldb.Float, nullable=False)
    swipes = sqldb.Column(sqldb.Integer, nullable=False)
    guest_swipes = sqldb.Column(sqldb.Integer, nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())


class DiningTransaction(sqldb.Model):
    id = sqldb.Column(sqldb.Integer, primary_key=True)
    account_id = sqldb.Column(sqldb.VARCHAR(255), sqldb.ForeignKey("account.id"))
    date = sqldb.Column(sqldb.DateTime, nullable=False)
    description = sqldb.Column(sqldb.Text, nullable=False)
    amount = sqldb.Column(sqldb.Float, nullable=False)
    balance = sqldb.Column(sqldb.Float, nullable=False)
    created_at = sqldb.Column(sqldb.DateTime, server_default=sqldb.func.now())
"""
>>>>>>> d3f6306d09f285f0293e8c0148e17a34e80ff3d1
