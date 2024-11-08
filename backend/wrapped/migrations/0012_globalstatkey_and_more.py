# Generated by Django 5.0.2 on 2024-11-08 18:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wrapped', '0011_remove_page_semester_semester_pages'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalStatKey',
            fields=[
                ('key', models.CharField(max_length=50, primary_key=True, serialize=False)),
            ],
        ),
        migrations.RenameField(
            model_name='globalstatthrough',
            old_name='GlobalStat',
            new_name='GlobalStatKey',
        ),
        migrations.AlterField(
            model_name='semester',
            name='pages',
            field=models.ManyToManyField(blank=True, to='wrapped.page'),
        ),
        migrations.AlterField(
            model_name='globalstat',
            name='key',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wrapped.globalstatkey'),
        ),
    ]
