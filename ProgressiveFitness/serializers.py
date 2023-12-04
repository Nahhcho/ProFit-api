from rest_framework import serializers
from .models import User, Workout, Exercise, Set

class SetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fileds = ['id', 'set_number', 'reps', 'weight']
    
class ExercisesSerializer(serializers.ModelSerializer):
    sets = SetSerializer(many=True)

    class Meta:
        model: Exercise
        fields = ['id', 'title', 'sets']

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = ExercisesSerializer(many=True)

    class Meta:
        model = Workout
        fields = ['id', 'title', 'exercises']

class UserSerializer(serializers.ModelSerializer):
    workouts = WorkoutSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'weight', 'age', 'workouts', 'username']
    
