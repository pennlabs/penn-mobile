# Generated by Django 4.0.1 on 2022-02-02 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0010_remove_post_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="portal/images"),
        ),
    ]
