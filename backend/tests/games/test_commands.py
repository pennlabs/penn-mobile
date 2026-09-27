from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from games.models import Game


MOCK_BOARD = [["a", "b", "c", "d", "e"]] * 5
MOCK_SEED = "garden"
MOCK_SOLS = ["cat", "cats", "table", "garden", "gardens"]


def mock_generate_good_game():
    return MOCK_BOARD, MOCK_SEED, MOCK_SOLS


class TestGenerateGameCommand(TestCase):
    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_creates_game_with_word_length_frequencies(self):
        call_command("generate_game")

        game = Game.objects.get(date=timezone.localdate())
        self.assertEqual(MOCK_BOARD, game.board)
        self.assertEqual(MOCK_SEED, game.seed)
        self.assertEqual(MOCK_SOLS, game.possible_words)
        self.assertEqual({"3": 1, "4": 1, "5": 1, "6": 1, "7": 1, "8": 0}, game.word_length_freq)

    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_running_twice_updates_same_record(self):
        call_command("generate_game")
        call_command("generate_game")

        self.assertEqual(1, Game.objects.filter(date=timezone.localdate()).count())
