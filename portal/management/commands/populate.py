import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from portal.models import Poll, PollOption, PollVote, TargetPopulation


# black -l100 .
# isort .
# flake8


def populate():
    User = get_user_model()
    user1 = User.objects.create_user("user1", "user@seas.upenn.edu", "user")
    user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
    user3 = User.objects.create_user("user3", "user3@seas.upenn.edu", "user3")
    admin = User.objects.create_superuser("admin@example.com", "admin", "admin")

    Poll.objects.create(
        user=user1,
        source="poll 1",
        question="poll question 1",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )

    # Poll that expired one day ago
    Poll.objects.create(
        user=user1,
        source="poll expired",
        question="lorem ipsum",
        expire_date=timezone.now() - datetime.timedelta(days=1),
        approved=True,
    )

    call_command("load_target_populations")
    target_pop_seas = TargetPopulation.objects.get(population="SEAS").id
    poll_targeting_seas = Poll.objects.create(
        user=user1,
        source="poll for seas",
        quesiton="cis major?",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    poll_targeting_seas.target_populations.add(target_pop_seas)

    target_pop_sas = TargetPopulation.objects.get(population="College").id
    poll_targeting_seas_sas = Poll.objects.create(
        user=user1,
        source="poll for seas",
        quesiton="cis major?",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    poll_targeting_seas_sas.target_populations.add(target_pop_seas)
    poll_targeting_seas_sas.target_populations.add(target_pop_sas)

    Poll.objects.create(
        user=user1,
        source="poll 1",
        question="poll question 1",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=False,
    )

    # Poll with 2 options
    poll_with_options = Poll.objects.create(
        user=user1,
        source="options",
        question="poll option 2",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    PollOption.objects.create(poll=poll_with_options, choice="choice 1")
    PollOption.objects.create(poll=poll_with_options, choice="choice 2")

    Poll.objects.create(
        user=user1,
        source="options",
        question="poll option 2",
        image_url="https://pbs.twimg.com/media/B3hTc0kIUAA0mzA.jpg",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )

    # Poll with 2 options with 2 votes for option 1 and 1 vote for option 2
    # Creator votes the poll
    poll_with_options_and_votes = Poll.objects.create(
        user=user1,
        source="options",
        question="poll option 2",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    option_1_for_votes = PollOption.objects.create(
        poll=poll_with_options_and_votes, choice="choice 1"
    )
    option_2_for_votes = PollOption.objects.create(
        poll=poll_with_options_and_votes, choice="choice 2"
    )
    vote_1 = PollVote.objects.create(
        user=user1, poll=poll_with_options_and_votes, created_date=datetime.now()
    )
    vote_1.poll_options.add(option_1_for_votes)
    vote_1.poll_options.add(option_2_for_votes)
    vote_2 = PollVote.objects.create(
        user=user1, poll=poll_with_options_and_votes, created_date=datetime.now()
    )
    vote_2.poll_options.add(option_1_for_votes)

    # UNAPPROVED Poll with 2 options with 2 votes for option 1 and 1 vote for option 2
    # Creator votes for the poll
    unapproved_poll_with_options_and_votes = Poll.objects.create(
        user=user1,
        source="options",
        question="poll option 2",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=False,
    )
    unapproved_option_1_for_votes = PollOption.objects.create(
        poll=unapproved_poll_with_options_and_votes, choice="choice 1"
    )
    unapproved_option_2_for_votes = PollOption.objects.create(
        poll=unapproved_poll_with_options_and_votes, choice="choice 2"
    )
    unapproved_vote_1 = PollVote.objects.create(
        user=user1, poll=unapproved_poll_with_options_and_votes, created_date=datetime.now()
    )
    unapproved_vote_1.poll_options.add(unapproved_option_1_for_votes)
    unapproved_vote_1.poll_options.add(unapproved_option_2_for_votes)
    unapproved_vote_2 = PollVote.objects.create(
        user=user1, poll=unapproved_poll_with_options_and_votes, created_date=datetime.now()
    )
    unapproved_vote_2.poll_options.add(unapproved_option_1_for_votes)

    # Poll created by admin
    # Other students vote for the poll
    poll_admin = Poll.objects.create(
        user=admin,
        source="poll 1",
        question="poll question 1",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    option_1_for_votes_admin = PollOption.objects.create(poll=poll_admin, choice="choice 1")
    option_2_for_votes_admin = PollOption.objects.create(poll=poll_admin, choice="choice 2")
    admin_vote_1 = PollVote.objects.create(user=user1, poll=poll_admin, created_date=datetime.now())
    admin_vote_1.poll_options.add(option_1_for_votes_admin)
    admin_vote_2 = PollVote.objects.create(user=user2, poll=poll_admin, created_date=datetime.now())
    admin_vote_2.poll_options.add(option_2_for_votes_admin)

    # Poll created by student
    # Other students vote for the poll
    poll_with_options_and_votes_multi = Poll.objects.create(
        user=user3,
        source="options",
        question="poll option 2",
        expire_date=timezone.now() + datetime.timedelta(days=1),
        approved=True,
    )
    option_1_for_votes_multi = PollOption.objects.create(
        poll=poll_with_options_and_votes_multi, choice="choice 1"
    )
    option_2_for_votes_multi = PollOption.objects.create(
        poll=poll_with_options_and_votes_multi, choice="choice 2"
    )
    vote_1 = PollVote.objects.create(
        user=user1, poll=poll_with_options_and_votes_multi, created_date=datetime.now()
    )
    vote_1.poll_options.add(option_1_for_votes_multi)
    vote_1.poll_options.add(option_2_for_votes_multi)
    vote_2 = PollVote.objects.create(
        user=user2, poll=poll_with_options_and_votes_multi, created_date=datetime.now()
    )
    vote_2.poll_options.add(option_1_for_votes_multi)
