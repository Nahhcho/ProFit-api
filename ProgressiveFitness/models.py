from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    workouts = models.ManyToManyField('Workout', symmetrical=False, blank=True, default=None, null=True)
    weight = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

class Workout(models.Model):
    title = models.TextField(max_length=20)
    exercises = models.ManyToManyField('Exercise', symmetrical=False, blank=True, default=None, null=True)

    def __str__(self):
        return f"{self.title}"

class Exercise(models.Model):
    exercise_num = models.IntegerField()
    title = models.TextField(max_length=10)
    sets = models.ManyToManyField('Set', symmetrical=False, blank=True, default=None, null=True)

    def __str__(self):
        return f"Exercise {self.exercise_num}: {self.title}"

class Set(models.Model):
    set_num = models.IntegerField()
    reps = models.IntegerField()
    weight = models.DecimalField(max_digits=20, decimal_places=2, blank=True, default=0)

    def __str__(self):
        return f"Set {self.set_num}: {self.reps} x {self.weight}"

