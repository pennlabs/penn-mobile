from django.contrib import admin

from portal.models import Poll, PollOption, PollVote, TargetPopulation


admin.site.register(TargetPopulation)
admin.site.register(Poll)
admin.site.register(PollOption)
admin.site.register(PollVote)
