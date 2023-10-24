from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()


class Offer(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "sublet"], name="unique_offer")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers_made")
    sublet = models.ForeignKey("Sublet", on_delete=models.CASCADE, related_name="offers")
    # TODO: Make sure phone_number is being validated by serializers/frontend
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.sublet} made by {self.user}"


class Favorite(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "sublet"], name="unique_favorite")]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sublet = models.ForeignKey("Sublet", on_delete=models.CASCADE)


class Amenity(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Sublet(models.Model):
    subletter = models.ForeignKey(User, on_delete=models.CASCADE)
    sublettees = models.ManyToManyField(
        User, through=Offer, related_name="sublets_offered", null=True, blank=True
    )
    favorites = models.ManyToManyField(
        User, through=Favorite, related_name="sublets_favorited", null=True, blank=True
    )
    amenities = models.ManyToManyField(
        Amenity, null=True, blank=True
    )  # TODO: not sure if anything else should go into this as params

    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True, blank=True)
    beds = models.IntegerField(null=True, blank=True)
    baths = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    external_link = models.URLField(max_length=255)
    min_price = models.IntegerField()
    max_price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    # TODO: would a last updated datetime be helpful?
    expires_at = models.DateTimeField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} by {self.subletter}"


# Not sure how exactly things are handled S3-side, please review
class SubletImage(models.Model):
    # Not sure if Cascade deletes the image from servers or just the reference
    sublet = models.ForeignKey(Sublet, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="sublet/images")
