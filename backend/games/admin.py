from django.contrib import admin

from games.models import Game, GameUser, LeaderboardEntry


admin.site.register(Game)
admin.site.register(GameUser)
admin.site.register(LeaderboardEntry)
