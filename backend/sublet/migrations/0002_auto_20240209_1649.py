# Generated by Django 3.2.24 on 2024-02-09 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sublet", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(model_name="sublet", old_name="max_price", new_name="price",),
        migrations.RemoveField(model_name="sublet", name="min_price",),
        migrations.AddField(
            model_name="sublet", name="negotiable", field=models.BooleanField(default=True),
        ),
    ]