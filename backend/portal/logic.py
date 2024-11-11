import json
from collections import defaultdict
from typing import Any, Optional

from accounts.ipc import authenticated_request
from rest_framework.exceptions import PermissionDenied

from portal.models import Poll, PollOption, PollVote, TargetPopulation
from portal.types import PopulationGroups, PopulationList
from utils.types import DjangoUserType


def get_user_info(user: DjangoUserType) -> dict[str, Any]:
    """Returns Platform user information"""
    response = authenticated_request(user, "GET", "https://platform.pennlabs.org/accounts/me/")
    if response.status_code == 403:
        raise PermissionDenied("IPC request failed")
    return json.loads(response.content)


def get_user_clubs(user: DjangoUserType) -> list[dict[str, Any]]:
    """Returns list of clubs that user is a member of"""
    response = authenticated_request(user, "GET", "https://pennclubs.com/api/memberships/")
    if response.status_code == 403:
        raise PermissionDenied("IPC request failed")
    res_json = json.loads(response.content)
    return res_json


def get_club_info(user: DjangoUserType, club_code: str) -> dict[str, Any]:
    """Returns club information based on club code"""
    response = authenticated_request(user, "GET", f"https://pennclubs.com/api/clubs/{club_code}/")
    if response.status_code == 403:
        raise PermissionDenied("IPC request failed")
    res_json = json.loads(response.content)
    return {"name": res_json["name"], "image": res_json["image_url"], "club_code": club_code}


def get_user_populations(user: DjangoUserType) -> PopulationGroups:
    """Returns the target populations that the user belongs to"""

    user_info = get_user_info(user)

    year: PopulationList = (
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_YEAR, population=user_info["student"]["graduation_year"]
            )
        ]
        if user_info["student"]["graduation_year"]
        else []
    )

    school: PopulationList = (
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_SCHOOL, population=x["name"])
            for x in user_info["student"]["school"]
        ]
        if user_info["student"]["school"]
        else []
    )

    major: PopulationList = (
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_MAJOR, population=x["name"])
            for x in user_info["student"]["major"]
        ]
        if user_info["student"]["major"]
        else []
    )

    degree: PopulationList = (
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_DEGREE, population=x["degree_type"]
            )
            for x in user_info["student"]["major"]
        ]
        if user_info["student"]["major"]
        else []
    )

    return [year, school, major, degree]


def check_targets(obj: Poll, user: DjangoUserType) -> bool:
    """
    Check if user aligns with target populations of poll or post
    """

    population_groups = get_user_populations(user)

    year_targets = set(obj.target_populations.filter(kind=TargetPopulation.KIND_YEAR))
    school_targets = set(obj.target_populations.filter(kind=TargetPopulation.KIND_SCHOOL))
    major_targets = set(obj.target_populations.filter(kind=TargetPopulation.KIND_MAJOR))
    degree_targets = set(obj.target_populations.filter(kind=TargetPopulation.KIND_DEGREE))

    return all(
        set(group).issubset(targets)
        for group, targets in zip(
            population_groups, [year_targets, school_targets, major_targets, degree_targets]
        )
    )


def get_demographic_breakdown(poll_id: Optional[int] = None) -> list[dict[str, Any]]:
    """Collects Poll statistics on school and graduation year demographics"""
    if poll_id is None:
        raise ValueError("poll_id is required")
    # passing in id is necessary because
    # poll info is already serialized
    poll = Poll.objects.get(id=poll_id)
    data = []

    # gets all options for the poll
    options = PollOption.objects.filter(poll=poll)
    for option in options:
        context = {"option": option.choice, "breakdown": defaultdict(lambda: defaultdict(int))}
        # gets all votes for the option
        votes = PollVote.objects.filter(poll_options__in=[option])
        for vote in votes:
            # goes through each vote and adds +1 to the
            # target populations that the voter belongs to
            for target_population in vote.target_populations.all():
                context["breakdown"][target_population.kind][target_population.population] += 1
        data.append(context)
    return data
