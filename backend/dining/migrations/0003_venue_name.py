# Generated by Django 4.0.3 on 2022-10-08 03:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dining", "0002_diningitem_diningstation_diningmenu"),
    ]

    operations = [
        migrations.AddField(
            model_name="venue",
            name="name",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
