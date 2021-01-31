from django.contrib import admin

from laundry.models import Hall, LaundryRoom, LaundrySnapshot


admin.site.register(LaundryRoom)
admin.site.register(LaundrySnapshot)
admin.site.register(Hall)
