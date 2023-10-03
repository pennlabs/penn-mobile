from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


User = get_user_model()

class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers_made")
    sublet = models.ForeignKey("Sublet", on_delete=models.CASCADE, related_name="offers")
    #TODO: check if the way we're handling phone/email is fine, validate on frontend/routes that at least one is not null
    email = models.EmailField(max_length=255, null=True)
    phone_number = models.CharField(max_length=20, null=True)
    message = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.sublet} made by {self.user}"

class Amenity(models.Model):
    name = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.name

class Sublet(models.Model):
    subletter = models.ForeignKey(User, on_delete=models.CASCADE)
    sublettees = models.ManyToManyField(User, through=Offer, related_name="sublets_offered")
    amenities = models.ManyToManyField(Amenity)  # TODO: not sure if anything else should go into this as params

    title = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    beds = models.IntegerField()
    baths = models.IntegerField()
    description = models.TextField()
    external_link = models.CharField(max_length=255, null=True)
    min_price = models.IntegerField()
    max_price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    #TODO: would a last updated datetime be helpful?
    close_at = models.DateTimeField()
    #TODO: do we need time or just date on these starts?
    sublet_start_date = models.DateField()
    sublet_end_date = models.DateField()

    def __str__(self):
        return f"{self.title} by {self.subletter}"

#Not sure how exactly things are handled S3-side, please review
class Image(models.Model):
    #Not sure if Cascade deletes the image from servers or just the reference
    sublet = models.ForeignKey(Sublet, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="subletting/images")