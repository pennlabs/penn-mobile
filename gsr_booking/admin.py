from django.contrib import admin

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking

admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(GSR)
admin.site.register(GSRBooking)
