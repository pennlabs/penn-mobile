# Generated by Django 4.0.1 on 2022-03-25 21:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("penndata", "0004_remove_fitnesssnapshot_percent"),
    ]

    operations = [
        migrations.RenameField(
            model_name="fitnesssnapshot", old_name="date_updated", new_name="date",
        ),
    ]