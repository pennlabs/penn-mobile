# Generated by Django 4.0.3 on 2022-04-13 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("penndata", "0003_analyticsevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="analyticsevent",
            name="data",
            field=models.CharField(max_length=255, null=True),
        ),
    ]
