from collections import Counter

from django.test import SimpleTestCase

from games.generator import (
    MIN_LEN,
    MAX_LEN,
    MIN_TOTAL_WORDS,
    SIX_LETTER_WORDS,
    WORD_SET,
    generate_game,
    generate_good_game,
    neighbors,
    solve_game,
)


class TestNeighbors(SimpleTestCase):
    """Tests the neighbors() grid adjacency helper (used on a 5x5 board, n=4)."""

    def test_corner_has_three_neighbors(self):
        result = list(neighbors(4, 0, 0))
        self.assertEqual(3, len(result))

    def test_edge_has_five_neighbors(self):
        # top edge, not a corner
        result = list(neighbors(4, 2, 0))
        self.assertEqual(5, len(result))

    def test_center_has_eight_neighbors(self):
        result = list(neighbors(4, 2, 2))
        self.assertEqual(8, len(result))

    def test_all_neighbors_within_bounds(self):
        for x in range(5):
            for y in range(5):
                for xx, yy in neighbors(4, x, y):
                    self.assertGreaterEqual(xx, 0)
                    self.assertLessEqual(xx, 4)
                    self.assertGreaterEqual(yy, 0)
                    self.assertLessEqual(yy, 4)

    def test_no_self_in_neighbors(self):
        for x in range(5):
            for y in range(5):
                self.assertNotIn((x, y), list(neighbors(4, x, y)))


class TestGenerateGame(SimpleTestCase):
    def setUp(self):
        self.game, self.seed = generate_game()

    def test_board_is_5x5(self):
        self.assertEqual(5, len(self.game))
        for row in self.game:
            self.assertEqual(5, len(row))

    def test_all_cells_are_single_lowercase_letters(self):
        for row in self.game:
            for cell in row:
                self.assertEqual(1, len(cell))
                self.assertTrue(cell.isalpha())
                self.assertEqual(cell, cell.lower())

    def test_seed_is_six_letter_word(self):
        self.assertEqual(6, len(self.seed))

    def test_seed_comes_from_word_list(self):
        self.assertIn(self.seed, SIX_LETTER_WORDS)

    def test_seed_letters_present_on_board(self):
        flat = [cell for row in self.game for cell in row]
        board_counts = Counter(flat)
        for letter, count in Counter(self.seed).items():
            self.assertGreaterEqual(
                board_counts[letter],
                count,
                f"Letter '{letter}' from seed not sufficiently present on board",
            )


class TestSolveGame(SimpleTestCase):
    def setUp(self):
        self.game, _ = generate_game()
        self.sols = solve_game(self.game)

    def test_all_words_in_word_set(self):
        for word in self.sols:
            self.assertIn(word, WORD_SET, f"'{word}' is not a valid word")

    def test_all_words_within_length_limits(self):
        for word in self.sols:
            self.assertGreaterEqual(len(word), MIN_LEN)
            self.assertLessEqual(len(word), MAX_LEN)

    def test_no_duplicate_words(self):
        self.assertEqual(len(self.sols), len(set(self.sols)))

    def test_results_sorted_by_length_desc_then_alpha(self):
        for i in range(len(self.sols) - 1):
            a, b = self.sols[i], self.sols[i + 1]
            if len(a) == len(b):
                self.assertLessEqual(a, b, f"Alphabetical order violated: {a!r} before {b!r}")
            else:
                self.assertGreater(
                    len(a), len(b), f"Length order violated: {a!r} (len {len(a)}) before {b!r} (len {len(b)})"
                )

    def test_empty_like_board_returns_only_valid_words(self):
        # A board filled with a single rare letter should return no spurious words
        board = [["z"] * 5 for _ in range(5)]
        result = solve_game(board)
        for word in result:
            self.assertIn(word, WORD_SET)


class TestGenerateGoodGame(SimpleTestCase):
    """End-to-end test for the full game generation pipeline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.game, cls.seed, cls.sols = generate_good_game()

    def test_board_is_5x5(self):
        self.assertEqual(5, len(self.game))
        for row in self.game:
            self.assertEqual(5, len(row))

    def test_meets_minimum_word_count(self):
        self.assertGreaterEqual(len(self.sols), MIN_TOTAL_WORDS)

    def test_all_solutions_are_valid_words(self):
        for word in self.sols:
            self.assertIn(word, WORD_SET)

    def test_seed_comes_from_word_list(self):
        self.assertIn(self.seed, SIX_LETTER_WORDS)
