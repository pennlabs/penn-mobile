# Generated by Django 3.2.7 on 2021-12-31 20:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("portal", "0004_post")]

    operations = [
        migrations.RenameField(model_name="poll", old_name="user_comment", new_name="club_comment"),
        migrations.RemoveField(model_name="poll", name="approved"),
        migrations.RemoveField(model_name="poll", name="source"),
        migrations.RemoveField(model_name="poll", name="user"),
        migrations.RemoveField(model_name="pollvote", name="user"),
        migrations.AddField(
            model_name="poll", name="club_code", field=models.CharField(blank=True, max_length=255)
        ),
        migrations.AddField(
            model_name="poll",
            name="status",
            field=models.CharField(
                choices=[("DRAFT", "Draft"), ("REVISION", "Revision"), ("APPROVED", "Approved")],
                default="DRAFT",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="pollvote",
            name="id_hash",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="pollvote",
            name="target_populations",
            field=models.ManyToManyField(blank=True, to="portal.TargetPopulation"),
        ),
        migrations.AlterField(
            model_name="poll",
            name="expire_date",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
