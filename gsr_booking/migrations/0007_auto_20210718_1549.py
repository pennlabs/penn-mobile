# Generated by Django 3.2.5 on 2021-07-18 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gsr_booking", "0006_auto_20210629_1657"),
    ]

    operations = [
        migrations.AddField(
            model_name="gsr",
            name="kind",
            field=models.CharField(
                choices=[("WHARTON", "Wharton"), ("LIBCAL", "Libcal")],
                default="LIBCAL",
                max_length=7,
            ),
        ),
        migrations.AlterField(
            model_name="gsr", name="gid", field=models.IntegerField(blank=True, null=True),
        ),
    ]
