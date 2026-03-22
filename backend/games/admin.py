from django.contrib import admin

from games.models import Game, LeaderboardEntry

admin.site.register(Game)
admin.site.register(LeaderboardEntry)
