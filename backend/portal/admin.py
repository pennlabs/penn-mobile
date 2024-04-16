from django.contrib import admin
from django.utils.html import escape, mark_safe

from portal.models import Content, Poll, PollOption, PollVote, Post, TargetPopulation


class ContentAdmin(admin.ModelAdmin):
    @admin.action(description="Set status to Approved")
    def action_approved(modeladmin, request, queryset):
        queryset.update(status=Content.STATUS_APPROVED)

    @admin.action(description="Set status to Draft")
    def action_draft(modeladmin, request, queryset):
        queryset.update(status=Content.STATUS_DRAFT)

    @admin.action(description="Set status to Revision")
    def action_revision(modeladmin, request, queryset):
        queryset.update(status=Content.STATUS_REVISION)

    actions = [action_approved, action_draft, action_revision]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(ar=Content.ACTION_REQUIRED_CONDITION).order_by(
            "-ar", "created_date"
        )

    def ar(self, obj):
        return obj.ar

    ar.boolean = True


class PostAdmin(ContentAdmin):
    def image_tag(instance, width):
        return mark_safe(
            f'<img src="%s" height="{width}" />' % escape(instance.image and instance.image.url)
        )

    def small_image(self, instance):
        return PostAdmin.image_tag(instance, 100)

    small_image.short_description = "Post Image"

    def large_image(self, instance):
        return PostAdmin.image_tag(instance, 300)

    large_image.short_description = "Post Image"

    readonly_fields = ("large_image",)
    list_display = (
        "title",
        "subtitle",
        "club_code",
        "club_comment",
        "start_date",
        "expire_date",
        "ar",
        "status",
        "small_image",
    )


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 0


class PollAdmin(ContentAdmin):
    inlines = [PollOptionInline]
    list_display = (
        "question",
        "club_code",
        "club_comment",
        "start_date",
        "expire_date",
        "ar",
        "status",
    )


admin.site.register(TargetPopulation)
admin.site.register(Poll, PollAdmin)
admin.site.register(PollVote)
admin.site.register(Post, PostAdmin)
