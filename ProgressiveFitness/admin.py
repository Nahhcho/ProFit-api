from django.contrib import admin
from .models import User, Exercise, Workout, Set

admin.site.register(User)
admin.site.register(Exercise)
admin.site.register(Workout)
admin.site.register(Set)
