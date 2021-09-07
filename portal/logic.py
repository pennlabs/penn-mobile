from django.contrib.auth import get_user_model

from portal.models import PollVote, TargetPopulation


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


def get_demographic_breakdown(poll):
    """Collects Poll statistics on school and graduation year demographics"""
    votes = PollVote.objects.filter(poll=poll)
    for vote in votes:
        for poll_option in votes.poll_options:
            print("hi")


def vote_patterns(poll):
    """Collects Poll statistics on voting patterns wrt time"""
    pass
