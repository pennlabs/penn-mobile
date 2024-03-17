# Generated by Django 5.0.2 on 2024-03-15 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sublet", "0004_alter_sublet_external_link"),
    ]

    operations = [
        migrations.AddField(
            model_name="sublet",
            name="is_draft",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="sublet",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="sublet",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="sublet",
            name="price",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="sublet",
            name="start_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
