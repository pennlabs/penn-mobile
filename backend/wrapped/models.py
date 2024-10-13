from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
User = get_user_model()


class GlobalStat(models.Model):

    stat_key = models.CharField(max_length=50, 
                                null=False, blank=False)
    
    stat_value = models.CharField(max_length=50, 
                                  null=False, blank=False)
    
    semester = models.CharField(max_length=5, null=False, blank=False)

    class Meta:
        unique_together = ("stat_key", "semester")

    def __str__(self):
        return f"Global -- {self.stat_key}-{str(self.semester)} : {self.stat_value}"


# Add a new model for keys 
class UserStatKey(models.Model):
    stat_key = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self) -> str:
        return self.stat_key


class IndividualStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stat_key = models.ForeignKey(UserStatKey, on_delete=models.CASCADE)

    stat_value = models.CharField(max_length=50, 
                                  null=False, blank=False)
    semester = models.CharField(max_length=5, null=False, blank=False)

    class Meta: 
        unique_together = ("stat_key", "semester", "user")

    def __str__(self) -> str:
        return f"User: {self.user} -- {self.stat_key}-{str(self.semester)} : {self.stat_value}"
    
class Template(models.Model):

    # Some file path
    name = models.CharField(max_length=10, null=False, blank=False)
    template_path = models.CharField(max_length=50, null=False, blank=False)
    num_fields = models.IntegerField()
    def __str__(self) -> str:
        return f"{self.name}"


class Page(models.Model):

    # How to do this, using individual vs stat_key ?

    template = models.ForeignKey(Template, on_delete=models.CASCADE, null=False, blank=False)
    IndividualStat = models.ManyToManyField(IndividualStat, blank=True)
    GlobalStat = models.ManyToManyField(GlobalStat, blank=True)
    
