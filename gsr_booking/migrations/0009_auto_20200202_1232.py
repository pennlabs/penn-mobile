# Generated by Django 3.0.2 on 2020-02-02 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gsr_booking", "0008_auto_20200202_1218"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gsrbookingcredentials",
            name="expiration_date",
            field=models.DateTimeField(null=True, verbose_name="session ID expiration date"),
        ),
    ]
