# Generated by Django 3.2.7 on 2022-01-13 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0006_auto_20220112_1529"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="status",
            field=models.CharField(
                choices=[("DRAFT", "Draft"), ("REVISION", "Revision"), ("APPROVED", "Approved")],
                default="DRAFT",
                max_length=30,
            ),
        ),
    ]