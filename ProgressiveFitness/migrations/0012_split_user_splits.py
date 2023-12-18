# Generated by Django 4.2.7 on 2023-12-15 23:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ProgressiveFitness", "0011_workout_volume"),
    ]

    operations = [
        migrations.CreateModel(
            name="Split",
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
                ("title", models.TextField(max_length=50)),
                ("schedule", models.JSONField(default=dict)),
            ],
        ),
        migrations.AddField(
            model_name="user",
            name="splits",
            field=models.ManyToManyField(
                blank=True, default=None, null=True, to="ProgressiveFitness.split"
            ),
        ),
    ]