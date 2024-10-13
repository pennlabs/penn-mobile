# from django.db.models.signals import m2m_changed
# from django.core.exceptions import ValidationError
# from django.db import transaction
# from django.dispatch import receiver
# from wrapped.models import Page

# @receiver(m2m_changed, sender=Page.IndividualStat.through)
# @receiver(m2m_changed, sender=Page.GlobalStat.through)
# def validate_stats(sender, instance, action, **kwargs):
#     if action == "post_add" or action == "post_remove" or action == "post_clear":
#         transaction.on_commit(lambda: perform_validation(instance))

# def perform_validation(instance):
#     individual_stat_count = instance.IndividualStat.count()
#     global_stat_count = instance.GlobalStat.count()
#     total_stat_count = individual_stat_count + global_stat_count

#     print(f"Total stat change: {total_stat_count}")
#     print(f"Individual stat change: {individual_stat_count}")
#     print(f"Global stat change: {global_stat_count}")

#     if total_stat_count != instance.template.num_fields:
#         raise ValidationError(
#             f"The total number of stats (IndividualStat + GlobalStat) "
#             f"must equal the template's num_fields value ({instance.template.num_fields})."
#         )

#     individual_semesters = set(instance.IndividualStat.values_list('semester', flat=True))
#     global_semesters = set(instance.GlobalStat.values_list('semester', flat=True))

#     all_semesters = individual_semesters.union(global_semesters)

#     if len(all_semesters) > 1:
#         raise ValidationError("All IndividualStat and GlobalStat entries must be from the same semester.")
