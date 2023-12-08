from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    workouts = models.ManyToManyField('Workout', symmetrical=False, blank=True, default=None, null=True)
    weight = models.IntegerField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

class Workout(models.Model):
    title = models.TextField(max_length=20)
    exercises = models.ManyToManyField('Exercise', symmetrical=False, blank=True, default=None, null=True)

    def __str__(self):
        return f"{self.title}"

class Exercise(models.Model):
    title = models.TextField(max_length=10)
    sets = models.ManyToManyField('Set', symmetrical=False, blank=True, default=None, null=True)

    def __str__(self):
        return f"{self.title}"

class Set(models.Model):
    reps = models.IntegerField()
    weight = models.IntegerField(blank=True, default=None, null=True)

    def __str__(self):
        return f"{self.reps} x {self.weight}"

