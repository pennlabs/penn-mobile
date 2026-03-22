from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from games.models import Game


# 190 words spanning lengths 3–7 to exercise all freq buckets
MOCK_BOARD = [["a", "b", "c", "d", "e"]] * 5
MOCK_SEED = "garden"
MOCK_SOLS = (
    ["cat", "bat", "rat", "hat", "mat", "sat", "fat", "pat", "vat", "lat"] * 10  # 100 × len-3
    + ["cats", "bats", "rats", "hats", "mats"] * 10                               #  50 × len-4
    + ["table", "cable", "fable", "sable"] * 5                                    #  20 × len-5
    + ["garden"] * 10                                                              #  10 × len-6
    + ["gardens"] * 10                                                             #  10 × len-7
)  # total: 190


def mock_generate_good_game():
    return MOCK_BOARD, MOCK_SEED, MOCK_SOLS


class TestGenerateGameCommand(TestCase):
    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_creates_game_for_today(self):
        call_command("generate_game")
        self.assertTrue(Game.objects.filter(date=timezone.localdate()).exists())

    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_saves_correct_board_seed_and_words(self):
        call_command("generate_game")
        game = Game.objects.get(date=timezone.localdate())
        self.assertEqual(MOCK_BOARD, game.board)
        self.assertEqual(MOCK_SEED, game.seed)
        self.assertEqual(MOCK_SOLS, game.possible_words)

    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_computes_word_freqs_by_length(self):
        call_command("generate_game")
        game = Game.objects.get(date=timezone.localdate())
        # Django JSONField round-trips integer keys as strings
        expected = {"3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0}
        for w in MOCK_SOLS:
            expected[str(len(w))] += 1
        self.assertEqual(expected, game.freqs)

    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_running_twice_updates_same_record(self):
        call_command("generate_game")
        call_command("generate_game")
        self.assertEqual(1, Game.objects.filter(date=timezone.localdate()).count())

    @mock.patch(
        "games.management.commands.generate_game.generate_good_game", mock_generate_good_game
    )
    def test_prints_success_message(self):
        out = StringIO()
        call_command("generate_game", stdout=out)
        self.assertIn("Game generated successfully", out.getvalue())
