from rest_framework import serializers

from games.models import Game, LeaderboardEntry


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["date", "board", "possible_words"]


class GameDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = LeaderboardEntry
        fields = ["username", "score", "words_found", "submitted_at"]
