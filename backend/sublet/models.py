import datetime

from django.contrib.auth import get_user_model
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Offer(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "sublet"], name="unique_offer")]

    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="offers_made"
    )
    sublet: models.ForeignKey = models.ForeignKey(
        "Sublet", on_delete=models.CASCADE, related_name="offers"
    )
    email: str = models.EmailField(max_length=255, null=True, blank=True)
    phone_number: PhoneNumberField = PhoneNumberField(null=True, blank=True)
    message: str = models.CharField(max_length=255, blank=True)
    created_date: datetime.datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.sublet} made by {self.user}"


class Amenity(models.Model):
    name: str = models.CharField(max_length=255, primary_key=True)

    def __str__(self) -> str:
        return self.name


class Sublet(models.Model):
    subletter: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    sublettees: models.ManyToManyField = models.ManyToManyField(
        User, through=Offer, related_name="sublets_offered", blank=True
    )
    favorites: models.ManyToManyField = models.ManyToManyField(
        User, related_name="sublets_favorited", blank=True
    )
    amenities: models.ManyToManyField = models.ManyToManyField(Amenity, blank=True)

    title: str = models.CharField(max_length=255)
    address: str = models.CharField(max_length=255, null=True, blank=True)
    beds: int = models.IntegerField(null=True, blank=True)
    baths: float = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    description: str = models.TextField(null=True, blank=True)
    external_link: str = models.URLField(max_length=255, null=True, blank=True)
    price: int = models.IntegerField()
    negotiable: bool = models.BooleanField(default=True)
    created_at: datetime.datetime = models.DateTimeField(auto_now_add=True)
    expires_at: datetime.datetime = models.DateTimeField()
    start_date: datetime.date = models.DateField()
    end_date: datetime.date = models.DateField()

    def __str__(self) -> str:
        return f"{self.title} by {self.subletter}"


class SubletImage(models.Model):
    sublet: models.ForeignKey = models.ForeignKey(
        Sublet, on_delete=models.CASCADE, related_name="images"
    )
    image: models.ImageField = models.ImageField(upload_to="sublet/images")
