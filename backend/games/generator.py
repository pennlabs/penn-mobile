import random
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
zip_file_path = BASE_DIR / "words.txt.zip"
extract_directory = BASE_DIR

if not zip_file_path.exists():
    raise FileNotFoundError(f"words.txt.zip not found at {zip_file_path}")

with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
    try:
        with zip_ref.open("words.txt") as file:
            ws = [line.decode("utf-8").strip() for line in file if line.strip()]
    except KeyError as ex:
        raise FileNotFoundError(f"words.txt is not in {zip_file_path}") from ex

MIN_LEN, MAX_LEN = 3, 8
MIN_TOTAL_WORDS = 175

WORD_SET = set()
PREFIX_SET = set()
SIX_LETTER_WORDS = []

for w in ws:
    w = w.lower()
    if not w.isalpha():
        continue
    if len(w) == 6:
        SIX_LETTER_WORDS.append(w)
    if MIN_LEN <= len(w) <= MAX_LEN:
        WORD_SET.add(w)
        for i in range(1, len(w) + 1):
            PREFIX_SET.add(w[:i])


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


def solve_game(game, min_len=MIN_LEN, max_len=MAX_LEN):
    n = len(game)
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    found = set()
    visited = [[False] * n for _ in range(n)]

    def dfs(r, c, s):
        s += game[r][c]
        if s not in PREFIX_SET:
            return
        if len(s) >= min_len and s in WORD_SET:
            found.add(s)
        if len(s) == max_len:
            return

        visited[r][c] = True
        for dr, dc in dirs:
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and not visited[rr][cc]:
                dfs(rr, cc, s)
        visited[r][c] = False

    for r in range(n):
        for c in range(n):
            dfs(r, c, "")

    results = sorted(found, key=lambda w: (-len(w), w))
    return results


def generate_good_game(min_total_words=MIN_TOTAL_WORDS):
    while True:
        game, seed = generate_game()
        sols = solve_game(game)
        if len(sols) >= min_total_words:
            return game, seed, sols
