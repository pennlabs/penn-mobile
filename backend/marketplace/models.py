from enum import Enum

from django.contrib.auth import get_user_model
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Offer(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "item"], name="unique_offer")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers_made")
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="offers")
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.item} made by {self.user}"


class Category(Enum):
    SUBLET = "sublet"
    APPLIANCE = "appliance"
    COOKWARE = "cookware"
    FOOD = "food"
    BOOK = "book"
    ELECTRONICS = "electronics"
    FURNITURE = "furniture"
    CLOTHING = "clothing"
    TRANSPORTATION = "transportation"
    ROOMDECOR = "roomdecor"
    SPORTS = "sports"
    TICKETS = "tickets"
    GIFTCARD = "giftcard"
    OTHER = "other"


class Tag(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class ValueTag(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class ItemTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.tag} for {self.item}"


class ItemTagValue(models.Model):
    tag = models.ForeignKey(ValueTag, on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.tag} for {self.item}"


class Item(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    buyers = models.ManyToManyField(User, through=Offer, related_name="items_offered", blank=True)
    favorites = models.ManyToManyField(User, related_name="items_favorited", blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    external_link = models.URLField(max_length=255, null=True, blank=True)
    price = models.IntegerField()
    negotiable = models.BooleanField(default=True)
    category = models.CharField(
        max_length=50, choices=[(category, category.value) for category in Category]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.title} by {self.seller}"


class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="marketplace/images")
