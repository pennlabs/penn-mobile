from django.contrib import admin

from portal.models import Poll, PollOption, PollStatus, PollVote


admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(PollVote)
admin.site.register(PollStatus)
