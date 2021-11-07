from django.contrib import admin

from gsr_booking.models import (
    GSR,
    Group,
    GroupMembership,
    GSRBooking,
    GSRBookingCredentials,
    Reservation,
)


class GSRBookingCredentialsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ["user"]}),
        ("Wharton GSR Credentials", {"fields": ["session_id", "expiration_date"]}),
    )

    list_display = ("user", "session_id", "expiration_date", "date_updated")
    list_filter = ["user", "expiration_date", "date_updated"]
    search_fields = ["user", "session_id", "expiration_date", "date_updated"]


admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GSR)
admin.site.register(GSRBooking)
admin.site.register(Reservation)
