from django.contrib import admin
from gsr_booking.models import Group, GroupMembership, GSRBookingCredentials


admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GSRBookingCredentials)
