from django.contrib import admin

from dining.models import DiningItem, DiningMenu, DiningStation, Venue


admin.site.register(Venue)
admin.site.register(DiningItem)
admin.site.register(DiningMenu)
admin.site.register(DiningStation)
