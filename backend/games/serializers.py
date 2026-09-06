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
    name = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardEntry
        fields = ["name", "score", "num_words_found", "submitted_at"]

    def get_name(self, obj):
        return (obj.user.get_full_name() or None) if obj.show_name else None
