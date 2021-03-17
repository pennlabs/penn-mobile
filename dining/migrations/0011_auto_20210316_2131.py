# Generated by Django 3.1.7 on 2021-03-17 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dining', '0010_auto_20210314_1802'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diningpreference',
            name='venue_id',
        ),
        migrations.AddField(
            model_name='diningpreference',
            name='venue',
            field=models.ManyToManyField(to='dining.Venue'),
        ),
    ]
