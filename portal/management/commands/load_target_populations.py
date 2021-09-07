from django.core.management.base import BaseCommand

from portal.models import TargetPopulation


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        populations = ["Wharton", "SEAS", "Nursing", "College", "2022", "2023", "2024", "2025"]

        for population in populations:
            TargetPopulation.objects.get_or_create(population=population)

        self.stdout.write("Uploaded Target Populations!")
