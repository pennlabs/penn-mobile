# Generated by Django 3.2.7 on 2021-09-24 21:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gsr_booking", "0003_gsr_gsrbooking"),
    ]

    operations = [
        migrations.DeleteModel(name="GSRBookingCredentials",),
    ]
