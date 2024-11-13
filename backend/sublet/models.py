from django.contrib.auth import get_user_model
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Offer(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "sublet"], name="unique_offer")]

    id: int
    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="offers_made"
    )
    sublet: models.ForeignKey = models.ForeignKey(
        "Sublet", on_delete=models.CASCADE, related_name="offers"
    )
    email: models.EmailField = models.EmailField(max_length=255, null=True, blank=True)
    phone_number: PhoneNumberField = PhoneNumberField(null=True, blank=True)
    message: models.CharField = models.CharField(max_length=255, blank=True)
    created_date: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Offer for {self.sublet} made by {self.user}"


class Amenity(models.Model):
    name: models.CharField = models.CharField(max_length=255, primary_key=True)

    def __str__(self) -> str:
        return self.name


class Sublet(models.Model):
    id: int
    subletter: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE)
    sublettees: models.ManyToManyField = models.ManyToManyField(
        User, through=Offer, related_name="sublets_offered", blank=True
    )
    favorites: models.ManyToManyField = models.ManyToManyField(
        User, related_name="sublets_favorited", blank=True
    )
    amenities: models.ManyToManyField = models.ManyToManyField(Amenity, blank=True)

    title: models.CharField = models.CharField(max_length=255)
    address: models.CharField = models.CharField(max_length=255, null=True, blank=True)
    beds: models.IntegerField = models.IntegerField(null=True, blank=True)
    baths: models.DecimalField = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    description: models.TextField = models.TextField(null=True, blank=True)
    external_link: models.URLField = models.URLField(max_length=255, null=True, blank=True)
    price: models.IntegerField = models.IntegerField()
    negotiable: models.BooleanField = models.BooleanField(default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    start_date: models.DateField = models.DateField()
    end_date: models.DateField = models.DateField()

    def __str__(self) -> str:
        return f"{self.title} by {self.subletter}"


class SubletImage(models.Model):
    id: int
    sublet: models.ForeignKey = models.ForeignKey(
        Sublet, on_delete=models.CASCADE, related_name="images"
    )
    image: models.ImageField = models.ImageField(upload_to="sublet/images")
