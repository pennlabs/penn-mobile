from django.contrib import admin

from sublet.models import Amenity, Favorite, Offer, Sublet, SubletImage


admin.site.register(Offer)
admin.site.register(Amenity)
admin.site.register(Sublet)
admin.site.register(SubletImage)
admin.site.register(Favorite)
