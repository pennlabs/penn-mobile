from django.contrib.auth import get_user_model
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


User = get_user_model()


class Offer(models.Model):
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "item"], name="unique_offer_market")]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer for {self.item} made by {self.user}"


class Category(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    
    def __str__(self):
        return self.name
    


class Tag(models.Model):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Item(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items_listed")
    buyers = models.ManyToManyField(
        User, through=Offer, related_name="items_offered", blank=True
    )
    tags = models.ManyToManyField(Tag, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    favorites = models.ManyToManyField(User, related_name="items_favorited", blank=True)

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    external_link = models.URLField(max_length=255, null=True, blank=True)
    price = models.FloatField()
    negotiable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.title} by {self.seller}"


class Sublet(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="sublet")
    address = models.CharField(max_length=255)
    beds = models.IntegerField()
    baths = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


# TODO: Verify that this S2 bucket exists. Check if we need to make it manually or will Django make it for us?
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="marketplace/images")