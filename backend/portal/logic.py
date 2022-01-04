import json

from accounts.ipc import authenticated_request
from django.contrib.auth import get_user_model

from portal.models import Poll, PollOption, PollVote, TargetPopulation


User = get_user_model()


def get_user_info(user):
    response = authenticated_request(user, "GET", "https://platform.pennlabs.org/accounts/me/")
    return json.loads(response.content)


def get_user_clubs(user):
    response = authenticated_request(user, "GET", "https://pennclubs.com/api/memberships/")
    res_json = json.loads(response.content)
    return res_json


def get_club_info(user, club_code):
    response = authenticated_request(user, "GET", f"https://pennclubs.com/api/clubs/{club_code}/")
    res_json = json.loads(response.content)
    return {"name": res_json["name"], "image": res_json["image_url"], "club_code": club_code}


def get_user_populations(user):
    """Returns the target populations that the user belongs to"""

    user_info = get_user_info(user)

    content = []
    content.extend(
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_YEAR, population=user_info["student"]["graduation_year"]
            )
        ]
    )
    content.extend(
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_SCHOOL, population=x["name"])
            for x in user_info["student"]["school"]
        ]
    )
    content.extend(
        [
            TargetPopulation.objects.get(kind=TargetPopulation.KIND_MAJOR, population=x["name"])
            for x in user_info["student"]["major"]
        ]
    )
    content.extend(
        [
            TargetPopulation.objects.get(
                kind=TargetPopulation.KIND_DEGREE, population=x["degree_type"]
            )
            for x in user_info["student"]["major"]
        ]
    )
    return content


def get_demographic_breakdown(poll_id):
    """Collects Poll statistics on school and graduation year demographics"""

    # passing in id is necessary because
    # poll info is already serialized
    poll = Poll.objects.get(id=poll_id)
    data = []
    breakdown = {}
    # adds all targeted populations into breakdown
    for target_population in poll.target_populations.all():
        breakdown[target_population.population] = 0

    # gets all options for the poll
    options = PollOption.objects.filter(poll=poll)
    for option in options:
        context = {"option": option.choice, "breakdown": breakdown.copy()}
        # gets all votes for the option
        votes = PollVote.objects.filter(poll_options__in=[option])
        for vote in votes:
            # goes through each vote and adds +1 to the
            # target populations that the voter belongs to
            for target_population in vote.target_populations.all():
                context["breakdown"][target_population.population] += 1
        data.append(context)
    return data
