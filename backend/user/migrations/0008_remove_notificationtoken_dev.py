# Generated by Django 4.1.2 on 2022-11-06 17:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0007_alter_notificationsetting_service"),
    ]

    operations = [
        migrations.RemoveField(model_name="notificationtoken", name="dev",),
    ]