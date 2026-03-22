from django.core.management.base import BaseCommand
from django.utils import timezone

from games.generator import generate_good_game
from games.models import Game


class Command(BaseCommand):
    help = "Generate and save 100 future Word Hunt games"

    def handle(self, *args, **kwargs):
        for i in range(100):
            future_date = timezone.localdate() + timezone.timedelta(days=i)
            game, seed, sols = generate_good_game()

            word_freqs = {3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
            for w in sols:
                word_freqs[len(w)] += 1

            Game.objects.update_or_create(
                date=future_date,
                defaults={
                    "board": game,
                    "possible_words": sols,
                    "seed": seed,
                    "freqs": word_freqs,
                },
            )

            self.stdout.write(f"Game for {future_date} generated successfully")
