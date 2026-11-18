from rest_framework import serializers

from games.models import Game, GameUser, LeaderboardEntry


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["date", "board", "possible_words"]


class GameDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class GameUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameUser
        fields = ["anonymized", "school", "major", "graduation_year"]
        read_only_fields = ["school", "major", "graduation_year"]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    rank = serializers.IntegerField(read_only=True, allow_null=True, default=None)

    class Meta:
        model = LeaderboardEntry
        fields = ["name", "score", "num_words_found", "submitted_at", "rank"]

    def get_name(self, obj):
        game_user = getattr(obj.user, "gameuser", None)
        if not game_user or game_user.anonymized:
            return None
        return obj.user.get_full_name() or None
