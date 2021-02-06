from django.contrib import admin

from laundry.models import LaundrySnapshot, LaundryRoom


admin.site.register(LaundrySnapshot)
admin.site.register(LaundryRoom)
