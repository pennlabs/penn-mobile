from django.contrib import admin

from subletting.models import Offer, Amenity, Sublet, Image

admin.site.register(Offer)
admin.site.register(Amenity)
admin.site.register(Sublet)
admin.site.register((Image))