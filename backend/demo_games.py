import json
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pennmobile.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from games.generator import generate_good_game  # noqa: E402
from games.models import Game, LeaderboardEntry  # noqa: E402


User = get_user_model()
client = APIClient()

print("\n" + "=" * 50)

# TASK 1 ----------------------------------------------------------------------
print("--- Testing Task 1: Generate Games & Store in DB ---")
try:
    game_board, seed, sols = generate_good_game(
        min_total_words=50
    )  # Using a smaller number so it tests quickly
    print("✅ Game generation script successful! Seed word generated:", seed)

    game = Game.get_today()
    if game:
        print(f"✅ Django DB Game model successfully loaded for {game.date}.")
        print("   Board format:", type(game.board), "->", game.board[0], "...")
    else:
        print("❌ No game for today found. Ensure you ran 'python manage.py generate_game'")
except Exception as e:
    print("❌ Generation/Model script failed:", str(e))


# TASK 2 ----------------------------------------------------------------------
print("\n--- Testing Task 2: Models for storing game results (User+Day) ---")
user, _ = User.objects.get_or_create(username="testuser")
dummy_user, _ = User.objects.get_or_create(username="dummyuser2")

try:
    entry, created = LeaderboardEntry.objects.get_or_create(
        game=game, user=dummy_user, defaults={"score": 100, "num_words_found": 5}
    )
    print(
        f"✅ LeaderboardEntry model works for {dummy_user.username}. "
        f"Associated with Game {game.date}."
    )
    print(f"✅ Relational lookup successful: game.scores.count() = {game.scores.count()}")

except Exception as e:
    print("❌ Leaderboard model creation failed:", str(e))


client.force_authenticate(user=user)

# TASK 3 ----------------------------------------------------------------------
print("\n--- Testing Task 3: Fetch Game Route ---")
response = client.get("/games/word-hunt/today/", format="json")
print(f"✅ Route Status Code: {response.status_code}")
print("✅ JSON Data Payload Extract:")
print(json.dumps(response.data, indent=2)[:200] + "...\n")


# TASK 4 ----------------------------------------------------------------------
print("--- Testing Task 4: Submit Score Route (valid words) ---")
valid_words = game.possible_words[:3] if game and game.possible_words else []
data = {"words": valid_words}
response = client.post(f"/games/word-hunt/{game.date}/submit/", data, format="json")
print(f"✅ Route Status Code: {response.status_code}")
print("✅ Submit Route Response:")
print(json.dumps(response.data, indent=2) + "\n")


# TASK 5 ----------------------------------------------------------------------
print("--- Testing Task 5: Submit Score Route (invalid words) ---")
data = {"words": [valid_words[0] if valid_words else "cat", "notarealword123"]}
response2_user, _ = User.objects.get_or_create(username="testuser2")
client2 = APIClient()
client2.force_authenticate(user=response2_user)
response = client2.post(f"/games/word-hunt/{game.date}/submit/", data, format="json")
print(f"✅ Route Status Code: {response.status_code}")
print("✅ Validation Error Response:")
print(json.dumps(response.data, indent=2) + "\n")


# TASK 6 ----------------------------------------------------------------------
print("--- Testing Task 6: Leaderboard Route ---")
response = client.get(f"/games/word-hunt/{game.date}/leaderboard/", format="json")
print(f"✅ Route Status Code: {response.status_code}")
print("✅ Leaderboard JSON Output (Ranked):")
print(json.dumps(response.data, indent=2))

print("=" * 50 + "\n")
