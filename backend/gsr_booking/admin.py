from typing import Any, cast

from django.contrib import admin
from django.db.models import Manager, QuerySet
from django.http import HttpRequest

from gsr_booking.models import GSR, Group, GroupMembership, GSRBooking, Reservation
from utils.types import UserType


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0

    readonly_fields = ["name"]

    def name(self, obj: GroupMembership) -> str:
        user = cast(UserType, obj.user)
        return str(user.get_full_name())

    def get_fields(self, request: HttpRequest, obj: Any = None) -> list[str]:
        fields = super().get_fields(request, obj)
        to_remove = ["user", "name"]
        return ["name"] + [str(f) for f in fields if f not in to_remove]


class GroupAdmin(admin.ModelAdmin):
    search_fields = ["name__icontains"]
    list_display = ["name"]
    ordering = ["name"]

    inlines = [GroupMembershipInline]


class GroupMembershipAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "group__name__icontains"]


class GSRAdmin(admin.ModelAdmin):
    def get_queryset(self, request: HttpRequest) -> QuerySet[GSR, Manager[GSR]]:
        return GSR.all_objects.all()

    list_display = ["name", "kind", "lid", "gid", "in_use"]
    search_fields = ["name", "lid", "gid"]
    ordering = ["-in_use"]


admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(GSR, GSRAdmin)
admin.site.register(GSRBooking)
admin.site.register(Reservation)
