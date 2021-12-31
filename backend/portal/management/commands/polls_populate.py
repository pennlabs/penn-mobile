"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from portal.models import Poll, PollOption, PollVote, TargetPopulation
from user.models import Profile


User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        # Define graduation years
        df_2022 = datetime.date(2022, 5, 15)
        df_2023 = datetime.date(2023, 5, 16)
        df_2024 = datetime.date(2024, 5, 15)
        df_2025 = datetime.date(2025, 5, 17)

        # Create users and set graduation years
        if not User.objects.filter(username="user1").first():
            user1 = User.objects.create_user("user1", "user@seas.upenn.edu", "user")
            user1_profile = Profile.objects.get(user=user1)
            user1_profile.expected_graduation = df_2022
            user1_profile.save()
        else:
            user1 = User.objects.get(username="user1")

        if not User.objects.filter(username="user2").first():
            user2 = User.objects.create_user("user2", "user2@seas.upenn.edu", "user2")
            user2_profile = Profile.objects.get(user=user2)
            user2_profile.expected_graduation = df_2023
            user2_profile.save()
        else:
            user2 = User.objects.get(username="user2")

        if not User.objects.filter(username="user3").first():
            user3 = User.objects.create_user("user3", "user3@seas.upenn.edu", "user3")
            user3_profile = Profile.objects.get(user=user3)
            user3_profile.expected_graduation = df_2024
            user3_profile.save()
        else:
            user3 = User.objects.get(username="user3")

        if not User.objects.filter(username="admin").first():
            admin = User.objects.create_superuser("admin", "admin@seas.upenn.edu", "admin")
        else:
            admin = User.objects.get(username="admin")

        if not User.objects.filter(username="user_cas").first():
            user_cas = User.objects.create_user("user_cas", "user@sas.upenn.edu", "user_cas")
            user_cas_profile = Profile.objects.get(user=user_cas)
            user_cas_profile.expected_graduation = df_2025
            user_cas_profile.save()
        else:
            user_cas = User.objects.get(username="user_cas")

        if not User.objects.filter(username="user_wh").first():
            user_wh = User.objects.create_user("user_wh", "user@wharton.upenn.edu", "user_wh")
            user_wh_profile = Profile.objects.get(user=user_wh)
            user_wh_profile.expected_graduation = df_2024
            user_wh_profile.save()
        else:
            user_wh = User.objects.get(username="user_wh")

        if not User.objects.filter(username="user_nursing").first():
            user_nursing = User.objects.create_user(
                "user_nursing", "user@nursing.upenn.edu", "user_nursing"
            )
            user_nursing_profile = Profile.objects.get(user=user_nursing)
            user_nursing_profile.expected_graduation = df_2023
            user_nursing_profile.save()
        else:
            user_nursing = User.objects.get(username="user_nursing")

        # Create target populations
        call_command("load_target_populations")
        target_pop_seas = TargetPopulation.objects.get(
            population="School of Engineering and Applied Science"
        ).id
        target_pop_sas = TargetPopulation.objects.get(population="School of Arts & Sciences").id
        target_pop_wh = TargetPopulation.objects.get(population="The Wharton School").id
        target_pop_nursing = TargetPopulation.objects.get(population="School of Nursing").id
        target_pop_2022 = TargetPopulation.objects.get(population="2022").id
        target_pop_2023 = TargetPopulation.objects.get(population="2023").id
        target_pop_2024 = TargetPopulation.objects.get(population="2024").id
        target_pop_2025 = TargetPopulation.objects.get(population="2025").id

        # Poll that expired one day ago
        expired_poll, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll expired",
            question="lorem ipsum",
            expire_date=timezone.now() - datetime.timedelta(days=1),
            approved=True,
        )
        expired_poll.target_populations.add(target_pop_seas)
        option_1, _ = PollOption.objects.get_or_create(poll=expired_poll, choice="choice 1")
        option_2, _ = PollOption.objects.get_or_create(poll=expired_poll, choice="choice 2")

        # Poll without poll options, unapproved
        poll_no_option, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll_no_option",
            question="lorem ipsum",
            expire_date=timezone.now() - datetime.timedelta(days=1),
            approved=False,
        )
        poll_no_option.target_populations.add(target_pop_seas)

        # Poll without target populations, unapproved
        poll_no_target_pop, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll_no_target_pop",
            question="lorem ipsum",
            expire_date=timezone.now() - datetime.timedelta(days=1),
            approved=False,
        )
        poll_no_target_pop.target_populations.add(target_pop_seas)
        option_1, _ = PollOption.objects.get_or_create(poll=poll_no_target_pop, choice="choice 1")
        option_2, _ = PollOption.objects.get_or_create(poll=poll_no_target_pop, choice="choice 2")

        # Poll that targets seas students
        poll_targeting_seas, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll for seas",
            question="cis major?",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )
        poll_targeting_seas.target_populations.add(target_pop_seas)
        option_1, _ = PollOption.objects.get_or_create(poll=poll_targeting_seas, choice="choice 1")
        option_2, _ = PollOption.objects.get_or_create(poll=poll_targeting_seas, choice="choice 2")

        # Poll that targets seas and cas studnets
        poll_targeting_seas_sas, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll for seas and cas",
            question="seas or cas?",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )
        poll_targeting_seas_sas.target_populations.add(target_pop_seas)
        poll_targeting_seas_sas.target_populations.add(target_pop_sas)
        option_1, _ = PollOption.objects.get_or_create(
            poll=poll_targeting_seas_sas, choice="choice 1"
        )
        option_2, _ = PollOption.objects.get_or_create(
            poll=poll_targeting_seas_sas, choice="choice 2"
        )

        # Unapproved post
        unapproved_poll, _ = Poll.objects.get_or_create(
            user=user1,
            source="poll 1",
            question="poll question 1",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=False,
        )
        unapproved_poll.target_populations.add(target_pop_sas)
        option_1, _ = PollOption.objects.get_or_create(poll=unapproved_poll, choice="choice 1")
        option_2, _ = PollOption.objects.get_or_create(poll=unapproved_poll, choice="choice 2")

        # UNAPPROVED Poll with admin comment
        unapproved_poll_with_admin_comment, _ = Poll.objects.get_or_create(
            user=user1,
            source="options",
            question="question",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=False,
            admin_comment="Bad poll!",
        )
        unapproved_poll_with_admin_comment.target_populations.add(target_pop_seas)
        option_1, _ = PollOption.objects.get_or_create(
            poll=unapproved_poll_with_admin_comment, choice="choice 1"
        )
        option_2, _ = PollOption.objects.get_or_create(
            poll=unapproved_poll_with_admin_comment, choice="choice 2"
        )

        # Poll created by admin
        # cas, wh, seas and nursing students vote the poll
        poll_admin, _ = Poll.objects.get_or_create(
            user=admin,
            source="admin",
            question="poll for everyone",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
        )
        poll_admin.target_populations.add(target_pop_sas)
        poll_admin.target_populations.add(target_pop_wh)
        poll_admin.target_populations.add(target_pop_seas)
        poll_admin.target_populations.add(target_pop_nursing)
        option_1_for_votes_admin, _ = PollOption.objects.get_or_create(
            poll=poll_admin, choice="choice 1"
        )
        option_2_for_votes_admin, _ = PollOption.objects.get_or_create(
            poll=poll_admin, choice="choice 2"
        )
        poll_admin.save()
        vote_1, _ = PollVote.objects.get_or_create(
            user=user_cas, poll=poll_admin, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1_for_votes_admin)
        vote_2, _ = PollVote.objects.get_or_create(
            user=user_wh, poll=poll_admin, created_date=timezone.localtime()
        )
        vote_2.poll_options.add(option_2_for_votes_admin)
        vote_3, _ = PollVote.objects.get_or_create(
            user=user1, poll=poll_admin, created_date=timezone.localtime()
        )
        vote_3.poll_options.add(option_2_for_votes_admin)
        vote_4, _ = PollVote.objects.get_or_create(
            user=user_nursing, poll=poll_admin, created_date=timezone.localtime()
        )
        vote_4.poll_options.add(option_2_for_votes_admin)

        # Poll created by student, allows multiselect
        # Other seas students vote for the poll
        poll_with_options_and_votes_multi, _ = Poll.objects.get_or_create(
            user=user3,
            source="industry",
            question="cis or ese or dats?",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
        )
        poll_with_options_and_votes_multi.target_populations.add(target_pop_seas)
        option_1_for_votes_multi, _ = PollOption.objects.get_or_create(
            poll=poll_with_options_and_votes_multi, choice="choice 1"
        )
        option_2_for_votes_multi, _ = PollOption.objects.get_or_create(
            poll=poll_with_options_and_votes_multi, choice="choice 2"
        )
        vote_1, _ = PollVote.objects.get_or_create(
            user=user1, poll=poll_with_options_and_votes_multi, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1_for_votes_multi)
        vote_1.poll_options.add(option_2_for_votes_multi)
        vote_2, _ = PollVote.objects.get_or_create(
            user=user2, poll=poll_with_options_and_votes_multi, created_date=timezone.localtime()
        )
        vote_2.poll_options.add(option_1_for_votes_multi)

        # cas student creates poll targeted at wharton and nursing students
        poll_targeting_wh_nur, _ = Poll.objects.get_or_create(
            user=user_cas,
            source="poll for wharton and nursing",
            question="cis major?",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
        )
        poll_targeting_wh_nur.target_populations.add(target_pop_wh)
        poll_targeting_wh_nur.target_populations.add(target_pop_nursing)
        option_1, _ = PollOption.objects.get_or_create(poll=poll_targeting_wh_nur, choice="wharton")
        option_2, _ = PollOption.objects.get_or_create(poll=poll_targeting_wh_nur, choice="nursing")
        poll_targeting_wh_nur.save()
        vote_1, _ = PollVote.objects.get_or_create(
            user=user_wh, poll=poll_targeting_wh_nur, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1)
        vote_1.poll_options.add(option_2)
        vote_2, _ = PollVote.objects.get_or_create(
            user=user_nursing, poll=poll_targeting_wh_nur, created_date=timezone.localtime()
        )
        vote_2.poll_options.add(option_1)

        # Poll targeting wharton and nursing and class of 2022 and 2023
        poll_targeting_wh_nur_22_23, _ = Poll.objects.get_or_create(
            user=user_cas,
            source="poll for wharton and nursing, 2022-23",
            question="internship opportunities",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
        )
        poll_targeting_wh_nur_22_23.target_populations.add(target_pop_wh)
        poll_targeting_wh_nur_22_23.target_populations.add(target_pop_nursing)
        poll_targeting_wh_nur_22_23.target_populations.add(target_pop_2023)
        poll_targeting_wh_nur_22_23.target_populations.add(target_pop_2022)
        poll_targeting_wh_nur_22_23.save()
        option_1, _ = PollOption.objects.get_or_create(
            poll=poll_targeting_wh_nur_22_23, choice="wharton"
        )
        option_2, _ = PollOption.objects.get_or_create(
            poll=poll_targeting_wh_nur_22_23, choice="nursing"
        )
        vote_1, _ = PollVote.objects.get_or_create(
            user=user_wh, poll=poll_targeting_wh_nur_22_23, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1)
        vote_1.poll_options.add(option_2)
        vote_2, _ = PollVote.objects.get_or_create(
            user=user_nursing, poll=poll_targeting_wh_nur_22_23, created_date=timezone.localtime()
        )
        vote_3.poll_options.add(option_1)
        vote_3, _ = PollVote.objects.get_or_create(
            user=user2, poll=poll_targeting_wh_nur_22_23, created_date=timezone.localtime()
        )
        vote_3.poll_options.add(option_1)

        # Poll targeting the class of 2025
        poll_targeting_25, _ = Poll.objects.get_or_create(
            user=user_cas,
            source="poll for freshman",
            question="freshman internship opportunities",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
        )
        poll_targeting_25.target_populations.add(target_pop_2025)
        option_1, _ = PollOption.objects.get_or_create(poll=poll_targeting_25, choice="wharton")
        option_2, _ = PollOption.objects.get_or_create(poll=poll_targeting_25, choice="nursing")
        vote_1, _ = PollVote.objects.get_or_create(
            user=user_cas, poll=poll_targeting_25, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1)
        vote_1.poll_options.add(option_2)

        # Poll targeting wharton and the class of 2024
        poll_targeting_wh_24, _ = Poll.objects.get_or_create(
            user=user_cas,
            source="poll for wharton ppl",
            question="internship opportunities",
            expire_date=timezone.now() + datetime.timedelta(days=1),
            approved=True,
            multiselect=True,
        )
        poll_targeting_wh_24.target_populations.add(target_pop_wh)
        poll_targeting_wh_24.target_populations.add(target_pop_2024)
        poll_targeting_wh_24.save()
        option_1, _ = PollOption.objects.get_or_create(
            poll=poll_targeting_wh_24, choice="investment banking"
        )
        option_2, _ = PollOption.objects.get_or_create(poll=poll_targeting_wh_24, choice="trading")
        vote_1, _ = PollVote.objects.get_or_create(
            user=user_wh, poll=poll_targeting_wh_24, created_date=timezone.localtime()
        )
        vote_1.poll_options.add(option_1)
        vote_2.poll_options.add(option_2)
        vote_2, _ = PollVote.objects.get_or_create(
            user=user3, poll=poll_targeting_wh_24, created_date=timezone.localtime()
        )
        vote_2.poll_options.add(option_1)
        vote_2.poll_options.add(option_2)

        self.stdout.write("Uploaded Poll Objects!")
"""
