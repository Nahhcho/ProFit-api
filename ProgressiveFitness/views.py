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
            newExercise = Exercise(title=exercise['title'])
            newExercise.save()
            for set in exercise['sets']:
                newSet = Set(reps=set)
                newSet.user.add(user)
                newSet.save()
                newExercise.sets.add(newSet)
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
        weight = request.data.get('weight')
        user = User(pk=request.data.get('userId'))
        set_obj = Set(pk=id)
        set_obj.weight = weight
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
    else:
         return JsonResponse({"message": 'invalid credentials'}, status=401)
    
@api_view(['POST'])
def register(request):

        # Ensure password matches confirmation
        data = json.loads(request.body.decode('utf-8'))
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        name = data.get("name")

        # Attempt to create new user
        try:
            user = User.objects.create_user(username=username, password=password, first_name=name, email=email)
            user.save()

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)})
        except IntegrityError as e:
            print(e)
            return JsonResponse({'error': 'username already exists'})
    
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