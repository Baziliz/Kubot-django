# Generated by Django 5.0.6 on 2024-10-21 19:06

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_alter_discordprofile_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='onetimepassword',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
