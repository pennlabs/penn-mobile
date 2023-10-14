from django.contrib import admin
from django.utils.html import escape, mark_safe

from portal.models import Poll, PollOption, PollVote, Post, TargetPopulation


class PostAdmin(admin.ModelAdmin):
    def image_tag(self, instance):
        return mark_safe('<img src="%s" height="300" />' % escape(instance.image.url))

    image_tag.short_description = "Post Image"
    readonly_fields = ("image_tag",)


admin.site.register(TargetPopulation)
admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(PollVote)
admin.site.register(Post, PostAdmin)
