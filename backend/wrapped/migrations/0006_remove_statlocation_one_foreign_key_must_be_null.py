# Generated by Django 5.0.2 on 2024-10-18 21:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrapped', '0005_alter_statlocation_globalstatkey_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='statlocation',
            name='one_foreign_key_must_be_null',
        ),
    ]
