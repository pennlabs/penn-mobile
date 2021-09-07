from django.contrib.auth import get_user_model


# from portal.models import TargetPopulation
# from user.models import Profile
# TODO: write analytics logic here for poll creator and user history

User = get_user_model()


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
