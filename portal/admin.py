from django.contrib import admin

from portal.models import Poll, PollOption, PollVote


admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(PollVote)
