from django.contrib import admin

from laundry.models import Hall, LaundryRoom, LaundrySnapshot


admin.register(LaundryRoom)
admin.register(LaundrySnapshot)
admin.register(Hall)
