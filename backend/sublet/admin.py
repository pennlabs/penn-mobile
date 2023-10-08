from django.contrib import admin

from sublet.models import Offer, Amenity, Sublet, SubletImage, Favorite

admin.site.register(Offer)
admin.site.register(Amenity)
admin.site.register(Sublet)
admin.site.register(SubletImage)
admin.site.register(Favorite)