# Create your models here.

# create venues

class Venue(models.Model):
    venue_id = models.IntegerField()
    image_url = models.URLField()



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
