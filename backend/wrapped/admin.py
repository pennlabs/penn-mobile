from django.contrib import admin
from django.core.exceptions import ValidationError

from wrapped.models import GlobalStat, IndividualStat, UserStatKey, Template, Page


class WrappedIndividualAdmin(admin.ModelAdmin):
    search_fields = ["user__username__icontains", "stat_key__stat_key__icontains", "semester__icontains"]
    list_display = ["user", "stat_key", "stat_value", "semester"]


class WrappedGlobalAdmin(admin.ModelAdmin):
    
    list_display = ["stat_key", "stat_value", "semester"]
    search_fields = ["semester__icontains","stat_key__icontains"]



# class PageAdmin(admin.ModelAdmin):
#     # Customize the admin interface for YourModel if needed
#     list_display = ['template']  # Example field to display, modify as needed

#     def save_related(self, request, form, formsets, change):
#         super().save_related(request, form, formsets, change)

#         # After saving the many-to-many relations, perform validation
#         instance = form.instance
        
#         # Count the IndividualStat and GlobalStat entries
#         individual_stat_count = instance.IndividualStat.count()
#         global_stat_count = instance.GlobalStat.count()

#         print(individual_stat_count)

#         total_stat_count = individual_stat_count + global_stat_count

#         if total_stat_count != instance.template.num_fields:
#             raise ValidationError(
#                 f"The total number of stats (IndividualStat + GlobalStat) "
#                 f"must equal the template's num_fields value ({instance.template.num_fields})."
#             )

#         # Validate that all stats are from the same semester
#         individual_semesters = set(instance.IndividualStat.values_list('semester', flat=True))
#         global_semesters = set(instance.GlobalStat.values_list('semester', flat=True))

#         all_semesters = individual_semesters.union(global_semesters)

#         if len(all_semesters) > 1:
#             raise ValidationError("All IndividualStat and GlobalStat entries must be from the same semester.")

# Register the model with the custom admin class



# admin.site.register(WrappedIndividualAdmin, WrappedGlobalAdmin)
admin.site.register(IndividualStat, WrappedIndividualAdmin)
admin.site.register(GlobalStat, WrappedGlobalAdmin)
admin.site.register(UserStatKey)
admin.site.register(Template)
# admin.site.register(Page, PageAdmin)
admin.site.register(Page)




