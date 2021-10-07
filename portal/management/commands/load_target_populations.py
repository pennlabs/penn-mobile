import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import TargetPopulation


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # loads majors, years, schools, and degrees onto TargetPopulations
        # runs get_or_create to ensure no duplicates
        for major in self.get_majors():
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_MAJOR, population=major
            )
        for year in self.get_years():
            TargetPopulation.objects.get_or_create(kind=TargetPopulation.KIND_YEAR, population=year)
        for school in self.get_schools():
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_SCHOOL, population=school
            )
        for degree in self.get_degrees():
            TargetPopulation.objects.get_or_create(
                kind=TargetPopulation.KIND_DEGREE, population=degree
            )

        self.stdout.write("Uploaded Target Populations!")

    def contains_filters(self, listed_filters, desired_filters=set(), excluded_filters=set()):
        # ensure no excluded filters appear
        for curr_filter in excluded_filters:
            if curr_filter in listed_filters:
                return False

        # ensure at least one desired filter appears
        for curr_filter in desired_filters:
            if curr_filter in listed_filters:
                return True

        return False

    def get_majors(self):
        # scrapes majors from the official penn catalog of all programs
        resp = requests.get("https://catalog.upenn.edu/programs/")
        soup = BeautifulSoup(resp.content.decode("utf8"), "html5lib")

        bachelor_filter = "filter_6"
        master_filter = "filter_25"
        phd_filter = "filter_7"
        professional_filter = "filter_10"
        minor_filter = "filter_26"
        desired_filters = {bachelor_filter, master_filter, phd_filter, professional_filter}
        excluded_filters = {minor_filter}

        listed_majors = set()
        # iterate through all list tags with "item" in the class (all programs)
        for program in soup.find_all(
            "li", class_=lambda value: value and value.startswith("item ")
        ):
            curr_filter_list = program.attrs["class"]
            # check if entry meets relevant desired and excluded filter criteria
            if not self.contains_filters(
                curr_filter_list,
                desired_filters=desired_filters,
                excluded_filters=excluded_filters,
            ):
                continue

            # grab the major name
            major_name = program.find("span", class_="title").text
            listed_majors.add(major_name)
        return listed_majors

    def get_schools(self):
        # scrapes schools from the official penn catalog of all programs
        resp = requests.get("https://catalog.upenn.edu/programs/")

        soup = BeautifulSoup(resp.content.decode("utf8"), "html5lib")

        schools = set()

        # iterate through all list tags with "item" in the class (all programs)
        school_list = soup.find("div", id="cat11list")
        for curr_school in school_list.find_all("div"):
            school_name = curr_school.text
            schools.add(school_name)
        return schools

    def get_years(self):
        # creates new class year in August in preparation for upcoming school year
        return (
            [timezone.localtime().year + x for x in range(4)]
            if timezone.localtime().month < 8
            else [timezone.localtime().year + x for x in range(1, 5)]
        )

    def get_degrees(self):
        return ["BACHELORS", "MASTERS", "PHD", "PROFESSIONAL"]
