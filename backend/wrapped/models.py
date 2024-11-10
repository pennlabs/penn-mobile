from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from datetime import timedelta

User = get_user_model()


# Add a new model for keys 
class IndividualStatKey(models.Model):
    key = models.CharField(max_length=50, primary_key=True,null=False, blank=False)

    def __str__(self) -> str:
        return self.key
    
class GlobalStatKey(models.Model):
    key = models.CharField(max_length=50, primary_key=True,null=False, blank=False)

    def __str__(self) -> str:
        return self.key


class Semester(models.Model):
    semester = models.CharField(max_length=5, primary_key=True,null=False, blank=False)
    pages = models.ManyToManyField('Page', blank=True)

class GlobalStat(models.Model):

    key = models.ForeignKey(GlobalStatKey, on_delete=models.CASCADE)

    
    value = models.CharField(max_length=50, 
                                  null=False, blank=False)
    
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("key", "semester")

    def __str__(self):
        return f"Global -- {self.key}-{str(self.semester)} : {self.value}"



class IndividualStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.ForeignKey(IndividualStatKey, on_delete=models.CASCADE)

    value = models.CharField(max_length=50, 
                                  null=False, blank=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta: 
        unique_together = ("key", "semester", "user")

    def __str__(self) -> str:
        return f"User: {self.user} -- {self.key}-{str(self.semester)} : {self.value}"
    

class Page(models.Model):

    name = models.CharField(max_length=50, primary_key=True,null=False, blank=False)
    template_path = models.CharField(max_length=50, null=False, blank=False)
    individual_stats = models.ManyToManyField(IndividualStatKey, through="IndividualStatPageField", blank=True)
    global_stats = models.ManyToManyField(GlobalStatKey, through="GlobalStatPageField", blank=True)
    duration = models.DurationField(blank=True, default=timedelta(minutes=0))

    def __str__(self):
        return f"{self.name}"


class IndividualStatPageField(models.Model):
    individual_stat_key = models.ForeignKey(IndividualStatKey,null=False, blank=False, default=None ,on_delete=models.CASCADE)
    Page = models.ForeignKey(Page, null=False, blank=False, on_delete=models.CASCADE)
    text_field_name = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return f"{self.Page} -> {self.text_field_name} : {self.individual_stat_key}"


class GlobalStatPageField(models.Model):
    global_stat_key = models.ForeignKey(GlobalStatKey,null=False, blank=False, default=None ,on_delete=models.CASCADE)
    Page = models.ForeignKey(Page, null=False, blank=False, on_delete=models.CASCADE)
    text_field_name = models.CharField(max_length=50, null=False, blank=False)
    def __str__(self):
        return f"{self.Page} -> {self.text_field_name} : {self.global_stat_key}"


