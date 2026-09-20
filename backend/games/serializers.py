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
    rank = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardEntry
        fields = ["name", "score", "num_words_found", "submitted_at", "rank"]

    def get_rank(self, obj):
        return getattr(obj, "rank", None)

    def get_name(self, obj):
        if not self.context.get("show_names"):
            return None
        game_user = getattr(obj.user, "gameuser", None)
        if not game_user or not game_user.show_name:
            return None
        return obj.user.get_full_name() or None
