from django.contrib import admin

from laundry.models import LaundryRoom, LaundrySnapshot


admin.site.register(LaundrySnapshot)
admin.site.register(LaundryRoom)
