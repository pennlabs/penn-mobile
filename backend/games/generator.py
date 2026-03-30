import random
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
zip_file_path = BASE_DIR / "words.txt.zip"
extract_directory = BASE_DIR

if not zip_file_path.exists():
    raise FileNotFoundError(f"words.txt.zip not found at {zip_file_path}")

MAX_LEN = 8
MIN_TOTAL_WORDS = 175

WORD_SET = set()
PREFIX_SET = set()
SIX_LETTER_WORDS = []

with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
    try:
        with zip_ref.open("words.txt") as file:
            for line in file:
                if line.strip():
                    w = line.decode("utf-8").strip().lower()
                    if not w.isalpha():
                        continue
                    if len(w) == 6:
                        SIX_LETTER_WORDS.append(w)
                    if len(w) <= MAX_LEN:
                        WORD_SET.add(w)
                        for i in range(1, len(w) + 1):
                            PREFIX_SET.add(w[:i])
    except KeyError as ex:
        raise FileNotFoundError(f"words.txt is not in {zip_file_path}") from ex


def neighbors(n, x, y):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            xx, yy = x + dx, y + dy
            if 0 <= xx <= n and 0 <= yy <= n:
                yield xx, yy


def generate_game():
    letters = list("abcdefghijklmnopqrstuvwxyz")
    game = [[""] * 5 for _ in range(5)]
    n = 4

    seed_word = random.choice(SIX_LETTER_WORDS)
    curr_x, curr_y = random.randint(0, n), random.randint(0, n)

    for c in seed_word:
        game[curr_y][curr_x] = c
        options = [(xx, yy) for (xx, yy) in neighbors(n, curr_x, curr_y) if game[yy][xx] == ""]
        if not options:
            return generate_game()
        curr_x, curr_y = random.choice(options)

    for y in range(5):
        for x in range(5):
            if game[y][x] == "":
                game[y][x] = random.choice(letters)

    return game, seed_word


def solve_game(game, min_len=3, max_len=MAX_LEN):
    n = len(game)
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    found = set()

    for r in range(n):
        for c in range(n):
            stack = [(r, c, "", frozenset())]
            while stack:
                cr, cc, s, vis = stack.pop()
                s = s + game[cr][cc]
                if s not in PREFIX_SET:
                    continue
                if len(s) >= min_len and s in WORD_SET:
                    found.add(s)
                if len(s) == max_len:
                    continue
                vis = vis | {(cr, cc)}
                for dr, dc in dirs:
                    rr, nc = cr + dr, cc + dc
                    if 0 <= rr < n and 0 <= nc < n and (rr, nc) not in vis:
                        stack.append((rr, nc, s, vis))

    return sorted(found, key=lambda w: (-len(w), w))


def generate_good_game(min_total_words=MIN_TOTAL_WORDS):
    while True:
        game, seed = generate_game()
        sols = solve_game(game)
        if len(sols) >= min_total_words:
            return game, seed, sols
