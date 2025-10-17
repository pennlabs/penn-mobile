from django.contrib import admin

from wrapped.models import (
    GlobalStat,
    GlobalStatKey,
    GlobalStatPageField,
    IndividualStat,
    IndividualStatKey,
    IndividualStatPageField,
    Page,
    Semester,
)


class WrappedIndividualAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "key__key__icontains", "semester__icontains"]
    list_display = ["user", "key", "value", "semester"]


class WrappedGlobalAdmin(admin.ModelAdmin):

    list_display = ["key", "value", "semester"]
    search_fields = ["key__icontains"]


class IndividualStatPageFieldAdmin(admin.TabularInline):
    model = IndividualStatPageField
    extra = 1


class GlobalStatPageFieldAdmin(admin.TabularInline):
    model = GlobalStatPageField
    extra = 1


class PageAdmin(admin.ModelAdmin):
    inlines = [IndividualStatPageFieldAdmin, GlobalStatPageFieldAdmin]


admin.site.register(IndividualStat, WrappedIndividualAdmin)
admin.site.register(GlobalStat, WrappedGlobalAdmin)
admin.site.register(IndividualStatKey)
admin.site.register(GlobalStatKey)
admin.site.register(Page, PageAdmin)
admin.site.register(Semester)