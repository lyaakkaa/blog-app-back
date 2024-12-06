# Generated by Django 5.1.2 on 2024-11-17 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="activity",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="location",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
