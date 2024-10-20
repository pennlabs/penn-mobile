from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q

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
    
class StatLocation(models.Model):
    IndividualStatKey = models.ForeignKey(UserStatKey,null=True, blank=True, default=None ,on_delete=models.CASCADE)
    GlobalStatKey = models.ForeignKey(GlobalStat, null=True,blank=True,default=None,on_delete=models.CASCADE)

    text_field_name = models.CharField(max_length=50, null=False, blank=False)
    def save(self, *args, **kwargs):
        print(self.GlobalStatKey)
        if not self.GlobalStatKey:
            self.GlobalStatKey = None
        if not self.IndividualStatKey:
            self.IndividualStatKey = None
        if self.IndividualStatKey != None and self.GlobalStatKey != None:
            raise Exception("Gave two stat values")
        

        super(StatLocation, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.text_field_name} -> {self.IndividualStatKey} --> {self.GlobalStatKey}"

# Why do we want time? Ask Vincent 
class Page(models.Model):

    # How to do this, using individual vs stat_key ?
    name = models.CharField(max_length=50, null=False, blank=False)
    template_path = models.CharField(max_length=50, null=False, blank=False)
    stat_locations = models.ManyToManyField(StatLocation, blank=True)
    semester = models.CharField(max_length=5, null=False, blank=False)
    def __str__(self):
        return f"{self.name}"