# Generated by Django 5.0.2 on 2024-05-06 22:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dining", "0005_diningitem_allergens_diningitem_nutrition_info_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="diningmenu",
            name="stations",
        ),
        migrations.AlterField(
            model_name="diningitem",
            name="allergens",
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name="diningitem",
            name="description",
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name="diningitem",
            name="ingredients",
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name="diningitem",
            name="nutrition_info",
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name="diningstation",
            name="menu",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stations",
                to="dining.diningmenu",
            ),
        ),
    ]
