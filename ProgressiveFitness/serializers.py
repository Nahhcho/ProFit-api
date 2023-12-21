from rest_framework import serializers
from .models import User, Workout, Exercise, Set, Split

class SetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Set
        fields = ['id', 'reps', 'weight', 'set_num']
    
class ExercisesSerializer(serializers.ModelSerializer):
    sets = SetSerializer(many=True)

    class Meta:
        model = Exercise
        fields = ['id', 'title', 'sets', 'exercise_num']

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = ExercisesSerializer(many=True)

    class Meta:
        model = Workout
        fields = ['id', 'title', 'exercises', 'volume', 'completed_date', 'projected_day']

class SplitSerializer(serializers.ModelSerializer):
    schedule = serializers.DictField()

    class Meta:
        model = Split
        fields = ['id', 'title', 'schedule']

class UserSerializer(serializers.ModelSerializer):
    workouts = WorkoutSerializer(many=True)
    splits = SplitSerializer(many=True)
    current_split = SplitSerializer()

    class Meta:
        model = User
        fields = ['id', 'weight', 'age', 'workouts', 'username', 'first_name', 'splits', 'current_split', 'bench']
    
