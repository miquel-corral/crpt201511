# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-26 12:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crpt201511', '0003_auto_20160525_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentcityidchoicesothertx',
            name='name',
            field=models.CharField(max_length=250),
        ),
    ]
