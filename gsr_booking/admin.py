from django.contrib import admin

from gsr_booking.models import GroupMembership, Group

admin.site.register(Group)
admin.site.register(GroupMembership)
