from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q


User = get_user_model()


class StatKey(models.Model):
    key = models.CharField(max_length=50, primary_key=True, null=False, blank=False)

    def __str__(self) -> str:
        return self.key

    class Meta:
        abstract = True


class IndividualStatKey(StatKey):
    pass


class GlobalStatKey(StatKey):
    pass


class Semester(models.Model):
    semester = models.CharField(max_length=16, primary_key=False, null=False, blank=False)
    pages = models.ManyToManyField("Page", blank=True)
    current = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["semester"], name="semester_unique"),
            models.UniqueConstraint(
                fields=["current"],
                condition=Q(current=True),
                name="single_current_semester",
            ),
        ]

    def __str__(self):
        return self.semester


class GlobalStat(models.Model):

    key = models.ForeignKey(GlobalStatKey, on_delete=models.CASCADE)
    value = models.CharField(max_length=50, null=False, blank=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("key", "semester")

    def __str__(self):
        return f"Global -- {self.key}-{str(self.semester)} : {self.value}"


class IndividualStat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.ForeignKey(IndividualStatKey, on_delete=models.CASCADE)

    value = models.CharField(max_length=50, null=False, blank=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("key", "semester", "user")

    def __str__(self) -> str:
        return f"User: {self.user} -- {self.key}-{str(self.semester)} : {self.value}"


class Page(models.Model):

    name = models.CharField(max_length=50, primary_key=True, null=False, blank=False)
    id = models.IntegerField(null=False, blank=False)
    template_path = models.CharField(max_length=200, null=False, blank=False)
    individual_stats = models.ManyToManyField(
        IndividualStatKey, through="IndividualStatPageField", blank=True
    )
    global_stats = models.ManyToManyField(GlobalStatKey, through="GlobalStatPageField", blank=True)
    duration = models.DurationField(blank=True, null=True, default=timedelta(minutes=0))

    def __str__(self):
        return f"{self.name}"


class IndividualStatPageField(models.Model):
    individual_stat_key = models.ForeignKey(
        IndividualStatKey, null=False, blank=False, default=None, on_delete=models.CASCADE
    )
    page = models.ForeignKey(Page, null=False, blank=False, on_delete=models.CASCADE)
    text_field_name = models.CharField(max_length=50, null=False, blank=False)

    def get_value(self, user, semester):
        return (
            IndividualStat.objects.filter(
                user=user, key=self.individual_stat_key, semester=semester
            )
            .first()
            .value
        )

    def __str__(self):
        return f"{self.page} -> {self.text_field_name} : {self.individual_stat_key}"


class GlobalStatPageField(models.Model):
    global_stat_key = models.ForeignKey(
        GlobalStatKey, null=False, blank=False, default=None, on_delete=models.CASCADE
    )
    page = models.ForeignKey(Page, null=False, blank=False, on_delete=models.CASCADE)
    text_field_name = models.CharField(max_length=50, null=False, blank=False)

    def get_value(self, _user, semester):
        return (
            GlobalStat.objects.filter(key=self.global_stat_key.key, semester=semester).first().value
        )

    def __str__(self):
        return f"{self.page} -> {self.text_field_name} : {self.global_stat_key}"
