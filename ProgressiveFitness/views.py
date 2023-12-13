from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
from django.http import JsonResponse
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from .models import User, Exercise, Set, Workout
from .serializers import UserSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['GET', 'PUT'])
def user_detail(request, id):
    if request.method == 'GET':
        user = User.objects.get(pk=id)
        serialized_user = UserSerializer(user)
        return JsonResponse(serialized_user.data)
    elif request.method == 'PUT':
        user = User.objects.get(pk=id)
        workout = Workout(title=request.data.get('title'))
        workout.save()
        exercises = request.data.get('exercises')

        for exercise in exercises:
            newExercise = Exercise(title=exercise['title'], exercise_num=exercise['exercise_num'])
            newExercise.save()
            for set in exercise['sets']:
                newSet = Set(reps=set['reps'], set_num=set['set_num'])
                newSet.save()
                print(newSet)
                newExercise.sets.add(newSet)
            print(newExercise)
            workout.exercises.add(newExercise)
        user.workouts.add(workout)
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token['user'] = UserSerializer(user).data

        return Response({'access': str(access_token), 'refresh': str(refresh)})
    
@api_view(['PUT'])
def set_detail(request, id):
    if request.method == 'PUT':
        user = User.objects.get(pk=request.data.get('userId'))
        set_obj = Set.objects.get(pk=id)
        print(request.data.get('reps'))
        set_obj.reps = request.data.get('reps')
        set_obj.weight = request.data.get('weight')
        set_obj.save()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token['user'] = UserSerializer(user).data
        return Response({'access': str(access_token), 'refresh': str(refresh)})
    
@api_view(['PUT', 'DELETE'])
def workout_detail(request, id):
    if request.method == 'PUT':
        workout = Workout.objects.get(pk=id)
        workout.title = request.data.get('title')
        user = User.objects.get(pk=request.data.get('userId'))

        exercises = workout.exercises.all()

        for exercise in exercises:
            sets = exercise.sets.all()
            sets.delete()
            exercise.delete()

        exercises = request.data.get('exercises')

        exercise_count = 1
        for exercise in exercises:
            newExercise = Exercise(title=exercise['title'], exercise_num=exercise_count)
            exercise_count += 1
            newExercise.save()
            set_count = 1
            for set_data in exercise['sets']:
                newSet = Set(reps=set_data['reps'], set_num=set_count, weight=set_data['weight'])
                set_count += 1
                newSet.save()
                print(newSet)
                newExercise.sets.add(newSet)
            print(newExercise)
            workout.exercises.add(newExercise)

        workout.save()
        user.save()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token['user'] = UserSerializer(user).data

        return Response({'access': str(access_token), 'refresh': str(refresh)})
    
    elif request.method == 'DELETE':
        workout = Workout.objects.get(pk=id)
        workout.title = request.data.get('title')
        user = User.objects.get(pk=request.data.get('userId'))

        exercises = workout.exercises.all()

        for exercise in exercises:
            sets = exercise.sets.all()
            sets.delete()
            exercise.delete()

        workout.delete()
        user.save()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token['user'] = UserSerializer(user).data

        return Response({'access': str(access_token), 'refresh': str(refresh)})
    
    
@api_view(['POST'])
def login(request):
    data = json.loads(request.body.decode('utf-8'))
    username = data.get("username")
    password = data.get("password")
    user = authenticate(request, username=username, password=password)

    if user is not None:
        serialized_user = UserSerializer(user)
        return JsonResponse({'message': 'successful login!', 'user': serialized_user.data}, status=200)
    elif User.objects.get(username=username) == None:
        return JsonResponse({"message": 'Username does not exist!'}, status=401)
    else:
         return JsonResponse({"message": 'invalid credentials!'}, status=401)
    
@api_view(['POST'])
def register(request):

        # Ensure password matches confirmation
        data = json.loads(request.body.decode('utf-8'))
        username = data.get("username")
        password = data.get("password")
        cpassword = data.get("cpassword")
        email = data.get("email")
        name = data.get("name")

        if cpassword != password:
            return Response({'message': 'Passwords do not match!'})
        if password is '' or email is '' or name is '' or username is '':
            return Response({'message': 'Fields cannot be empty!'})

        # Attempt to create new user
        try:
            user = User.objects.create_user(username=username, password=password, first_name=name, email=email)
            user.save()

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'message': 'success', 'access': str(access_token), 'refresh': str(refresh)})
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Username already exists!'})
    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user'] = UserSerializer(user).data
        # ...

        return token
    
class MyTokenObtainPairView(TokenObtainPairView):
     serializer_class = MyTokenObtainPairSerializer