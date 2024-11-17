import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import TargetPopulation


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--years",
            type=str,
            help="Comma seperated years to use for get_years."
            "This is only used for testing currently.",
        )

    def handle(self, *args, **kwargs):
        # loads majors, years, schools, and degrees onto TargetPopulations
        # runs get_or_create to ensure no duplicates
        majors = requests.get("https://platform.pennlabs.org/accounts/majors/").json()
        schools = requests.get("https://platform.pennlabs.org/accounts/schools/").json()
        degrees = self.get_degrees()
        for major in majors:
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_MAJOR, population=major["name"]
            )
        for school in schools:
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_SCHOOL, population=school["name"]
            )
        for degree in degrees:
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_DEGREE, population=degree
            )
        for year in self.get_years(kwargs["years"]):
            TargetPopulation.objects.get_or_create(kind=TargetPopulation.KIND_YEAR, population=year)
        self.stdout.write("Uploaded Target Populations!")

    def get_degrees(self):
        return ["BACHELORS", "MASTERS", "PHD", "PROFESSIONAL"]

    def get_years(self, years):
        # creates new class year in August in preparation for upcoming school year
        if years is None:
            return (
                [timezone.localtime().year + x for x in range(4)]
                if timezone.localtime().month < 8
                else [timezone.localtime().year + x for x in range(1, 5)]
            )
        else:
            return [int(x) for x in years.split(",")]
