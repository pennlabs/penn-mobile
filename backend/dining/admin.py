from django.contrib import admin

from dining.models import (
    DiningBalance,
    DiningItem,
    DiningMenu,
    DiningStation,
    DiningTransaction,
    Venue,
)


admin.site.register(Venue)
admin.site.register(DiningTransaction)
admin.site.register(DiningBalance)
admin.site.register(DiningItem)
admin.site.register(DiningMenu)
admin.site.register(DiningStation)
