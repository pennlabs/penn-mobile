from django.contrib.auth import get_user_model

from portal.models import Poll, PollOption, PollVote, TargetPopulation


User = get_user_model()


def get_user_populations(user):
    """Returns the target populations that the user belongs to"""

    school = get_affiliation(user.email)
    school_id = (
        TargetPopulation.objects.get(population=school).id
        if TargetPopulation.objects.filter(population=school).exists()
        else -1
    )
    year = user.profile.expected_graduation.year if user.profile.expected_graduation else None
    year_id = (
        TargetPopulation.objects.get(population=year).id
        if TargetPopulation.objects.filter(population=year).exists()
        else -1
    )
    return (school_id, year_id)


def get_affiliation(email):
    """Gets the school based on user's email"""

    if "wharton" in email:
        return "Wharton"
    elif "seas" in email:
        return "SEAS"
    elif "sas" in email:
        return "SAS"
    elif "nursing" in email:
        return "Nursing"
    else:
        return "Other"


def get_demographic_breakdown(poll_id):
    """Collects Poll statistics on school and graduation year demographics"""

    # passing in id is necessary because
    # poll info is already serialized
    poll = Poll.objects.get(id=poll_id)
    data = []
    breakdown = {}
    for target_population in poll.target_populations.all():
        breakdown[target_population.population] = 0

    options = PollOption.objects.filter(poll=poll)
    for option in options:
        context = {"option": option.choice, "breakdown": breakdown.copy()}
        votes = PollVote.objects.filter(poll_options__in=[option])
        for vote in votes:
            user_populations = get_user_populations(vote.user)
            for user_population in user_populations:
                if user_population != -1:
                    population = TargetPopulation.objects.get(id=user_population).population
                    context["breakdown"][population] += 1
        data.append(context)
    return data
