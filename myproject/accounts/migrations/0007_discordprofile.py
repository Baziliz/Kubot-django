# Generated by Django 5.0.6 on 2024-10-09 11:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_grade_academic_year_alter_grade_subject_code_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discord_id', models.CharField(max_length=255, unique=True)),
                ('discord_username', models.CharField(max_length=255)),
                ('discord_discriminator', models.CharField(max_length=4)),
                ('avatar_url', models.URLField()),
                ('access_token', models.CharField(max_length=255)),
                ('refresh_token', models.CharField(blank=True, max_length=255, null=True)),
                ('expires_in', models.IntegerField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]