from django.contrib import admin

from subletting.models import Offer, Amenity, Sublet, SubletImage

admin.site.register(Offer)
admin.site.register(Amenity)
admin.site.register(Sublet)
admin.site.register(SubletImage)