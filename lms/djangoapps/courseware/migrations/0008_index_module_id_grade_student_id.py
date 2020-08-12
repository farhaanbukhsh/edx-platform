# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2020-07-29 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courseware', '0007_remove_done_index'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='studentmodule',
            index=models.Index(fields=[b'module_state_key', b'grade', b'student'], name=b'courseware_stats'),
        ),
    ]
