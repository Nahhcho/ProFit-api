from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    workouts = models.ManyToManyField('Workout', symmetrical=False, blank=True, default=None, null=True)
    weight = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    current_split = models.ForeignKey('Split', blank=True, null=True, on_delete=models.SET_NULL, related_name='User')
    splits = models.ManyToManyField('Split', symmetrical=False, blank=True, null=True, default=None)
    age = models.IntegerField(blank=True, null=True)
    bench = models.IntegerField(blank=True, null=True)

class Split(models.Model):
    title = models.TextField(max_length=50)
    schedule = models.JSONField(default=dict)

class Workout(models.Model):
    title = models.TextField(max_length=20)
    exercises = models.ManyToManyField('Exercise', symmetrical=False, blank=True, default=None, null=True)
    completed_date = models.DateField(blank=True, null=True)
    projected_day = models.TextField(max_length=1, blank=True, null=True)
    volume = models.DecimalField(blank=True, null=True, max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.title} ({self.id})"

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

