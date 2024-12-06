# Generated by Django 5.1.2 on 2024-12-06 16:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_alter_post_pub_date"),
    ]

    operations = [
        migrations.CreateModel(
            name="Friend",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "user1_name_for_user2",
                    models.CharField(
                        blank=True,
                        help_text="Name user1 assigns to user2",
                        max_length=100,
                        null=True,
                    ),
                ),
                (
                    "user2_name_for_user1",
                    models.CharField(
                        blank=True,
                        help_text="Name user2 assigns to user1",
                        max_length=100,
                        null=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user1",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="friends_with_user1",
                        to="api.user",
                    ),
                ),
                (
                    "user2",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="friends_with_user2",
                        to="api.user",
                    ),
                ),
            ],
            options={
                "unique_together": {("user1", "user2")},
            },
        ),
    ]