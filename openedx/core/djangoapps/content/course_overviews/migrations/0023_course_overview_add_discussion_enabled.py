# Generated by Django 2.2.15 on 2020-08-12 03:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0022_courseoverviewtab_is_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseoverview',
            name='discussion_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='historicalcourseoverview',
            name='discussion_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
