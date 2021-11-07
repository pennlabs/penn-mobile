from django.contrib.auth import get_user_model

from portal.models import Poll, PollOption, PollVote, TargetPopulation


User = get_user_model()


def get_user_populations(user):
    """Returns the target populations that the user belongs to"""

    school = None
    # school = get_affiliation(user.email)
    # checks if school is in the target population
    school_id = (
        TargetPopulation.objects.get(population=school).id
        if TargetPopulation.objects.filter(population=school).exists()
        else -1
    )
    # year = user.profile.expected_graduation.year if user.profile.expected_graduation else None
    year = None
    # checks if year is in the target population
    year_id = (
        TargetPopulation.objects.get(population=year).id
        if TargetPopulation.objects.filter(population=year).exists()
        else -1
    )
    return (school_id, year_id)


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
            # populations the user belongs to
            user_populations = get_user_populations(vote.user)
            for user_population in user_populations:
                if user_population != -1:
                    population = TargetPopulation.objects.get(id=user_population).population
                    context["breakdown"][population] += 1
        data.append(context)
    return data


"""
import tinify

    source_data = file.read()
    read_image = tinify.from_buffer(source_data)  # .resize(method='cover', width=600, height=300)
    aws_url = read_image.store(
        service="s3",
        aws_access_key_id=os.environ.get("AWS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_SECRET"),
        region="us-east-1",
        path="penn.mobile.portal/images/{}/{}-{}".format(account.name, timestamp, file.filename),
    ).location

    return jsonify({"image_url": aws_url})

NOTE: get the file from request.FILES
"""
