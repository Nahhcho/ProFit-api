from rest_framework.response import Response
from rest_framework.decorators import api_view
import json
from django.http import JsonResponse
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from .models import User, Exercise, Set, Workout, Split
from .serializers import UserSerializer, WorkoutSerializer
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework import status
from rest_framework.response import Response
import os
import openai

openai.api_key = os.getenv('OPEN_AI_KEY')

def workout_details(title, exercises):
    output = f"{title}: \n"
    for exercise in exercises:
        output += f"{exercise['exercise_title']}: \n"
        set_count = 1
        for set in exercise['sets']:
            output += f"set {set_count}: {set['reps']} reps \n"
            set_count += 1
    return output

def get_outputs_for_tool_call(tool_call):
    workout_title = json.loads(tool_call.function.arguments)['workout_title']
    exercises = json.loads(tool_call.function.arguments)['exercises']
    print({'title': workout_title, 'exercises': exercises})
    return {
        'tool_call_id': tool_call.id,
        'output': workout_details(workout_title, exercises)
    }

@api_view(['POST'])
def ask_derek(request, id):
    try:
        if request.method == 'POST':
            example_workout = ''
            user = User.objects.get(pk=id)
            message_content = request.data.get('message')
            assistant = openai.beta.assistants.retrieve(
                assistant_id="asst_JWj0UeJ3KCZN874racuUYnGL"
            )

            if not message_content:
                return Response({'error': 'Message content is empty'}, status=status.HTTP_400_BAD_REQUEST)

            if user.thread_id is None or user.thread_id == '':
                thread = openai.beta.threads.create()
                user.thread_id = thread.id
                user.save()
            else:
                thread = openai.beta.threads.retrieve(user.thread_id)

            message = openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message_content,
            )

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions=f"""You are a personal trainer AI named Derek who focuses on the 
                scientific literature of fitness to deliver expert advice. If asked for a workout use you create_workout function."""
            )
           
            while run.status != "completed":
                run = openai.beta.threads.runs.retrieve(
                    thread_id = thread.id,
                    run_id = run.id
                )
                if run.required_action:
                    break
        
            if run.required_action:
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                example_workout = json.loads(tool_calls[0].function.arguments)
                tool_outputs = map(get_outputs_for_tool_call, tool_calls)
                tool_outputs = list(tool_outputs)
                print(tool_outputs)

                run = openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

                while run.status != "completed":
                    run = openai.beta.threads.runs.retrieve(
                        thread_id = thread.id,
                        run_id = run.id
                    )
                    if run.required_action:
                        break

            messages = openai.beta.threads.messages.list(
                    thread_id=thread.id
                )     

            if messages.data:
                response_text = messages.data[0].content[0].text.value
                return Response({'response': response_text, 'modelWorkout': example_workout}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No response received from AI'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except User.DoesNotExist:
        return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def user_detail(request, id):
    if request.method == 'GET':
        try:
            user = User.objects.get(pk=id)
            serialized_user = UserSerializer(user)
            return JsonResponse(serialized_user.data, status=status.HTTP_200_OK)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    elif request.method == 'PUT':
        try:
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

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    
@api_view(['PUT'])
def set_detail(request, id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(pk=request.data.get('userId'))
            set_obj = Set.objects.get(pk=id)
            print(request.data.get('reps'))
            set_obj.reps = request.data.get('reps')
            set_obj.weight = request.data.get('weight')
            set_obj.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data
            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    
@api_view(['PUT', 'DELETE'])
def workout_detail(request, id):
    if request.method == 'PUT':
        try: 
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

            for split in user.splits.all():
                schedule = split.schedule
                for key in schedule:
                    if schedule[key] is not None and schedule[key]['id'] is workout.id:
                        schedule[key] = WorkoutSerializer(workout).data
                        split.save()
            
            workout.save()
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    
    elif request.method == 'DELETE':
        try:
            workout = Workout.objects.get(pk=id)
            user = User.objects.get(pk=request.data.get('userId'))

            exercises = workout.exercises.all()

            for exercise in exercises:
                sets = exercise.sets.all()
                sets.delete()
                exercise.delete()
            
            for split in user.splits.all():
                if split != None:
                    schedule = split.schedule
                    for key in schedule:
                        if schedule[key] is not None and schedule[key]['id'] is workout.id:
                            schedule[key] = None
                            split.save()

            workout.delete()
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)})
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    
@api_view(['PUT'])
def set_split(request, id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(pk=id)
            split = user.splits.get(pk=request.data.get('splitId'))
            user.current_split = split

            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)})
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'}, status=status.HTTP_201_CREATED)
        
@api_view(['PUT', 'DELETE'])
def split_detail(request, id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(pk=request.data.get('userId'))
            split = Split.objects.get(pk=id)

            split.title = request.data.get('title')
            day_split = request.data.get('schedule')

            for key in day_split:
                print(key)
                print(day_split[key])
                if day_split[key] is None:
                    split.schedule[key] = None
                else:
                    split.schedule[key] = WorkoutSerializer(Workout.objects.get(pk=day_split[key])).data
            
            split.save()
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'}, status=500)
    elif request.method == 'DELETE':
        try:
            user = User.objects.get(pk=request.data.get('userId'))
            split = Split.objects.get(pk=id)
            split.delete()

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)})
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'}, status=500)
    
@api_view(['POST'])
def create_split(request):
    if request.method == 'POST':
        try:
            split = Split(title=request.data.get('title'))
            user = User.objects.get(pk=request.data.get('userId'))
            day_splits = request.data.get('split')

            print(day_splits)
            for key in day_splits:
                print(key)
                print(day_splits[key])
                if day_splits[key] is None:
                    split.schedule[key] = None
                else:
                    split.schedule[key] = WorkoutSerializer(Workout.objects.get(pk=day_splits[key])).data

            split.save()
            user.splits.add(split)
            print(split)

            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})


@api_view(['PUT'])
def complete_workout(request, id):
    if request.method == 'PUT':
        try: 
            total_volume = 0
            user = User.objects.get(pk=request.data.get('userId'))
            workout = Workout.objects.get(pk=id)
            date = request.data.get('completed_date')

            try:
                workout_to_delete = user.workouts.get(completed_date=date)
                exercises = workout_to_delete.exercises.all()

                for exercise in exercises:
                    sets = exercise.sets.all()
                    sets.delete()
                    exercise.delete()

                workout_to_delete.delete()
            except Workout.DoesNotExist:
                pass

            completed_workout = Workout(title=workout.title, completed_date=date)
            completed_workout.save()
            
            for exercise in workout.exercises.all():
                completed_exercise = Exercise(title=exercise.title, exercise_num=exercise.exercise_num)
                completed_exercise.save()
                exercise_volume = 1
                for set in exercise.sets.all():
                    exercise_volume += set.reps * set.weight
                    completed_set = Set(set_num=set.set_num, reps=set.reps, weight=set.weight)
                    completed_set.save()
                    completed_exercise.sets.add(completed_set)
                total_volume += exercise_volume
                completed_workout.exercises.add(completed_exercise)
            completed_workout.volume = total_volume
            completed_workout.save()
            print(completed_workout.volume)

            if workout.volume is None or total_volume >= workout.volume:
                workout.volume = total_volume
                workout.save()
                for split in user.splits.all():
                    schedule = split.schedule
                    for key in schedule:
                        if schedule[key] is not None and schedule[key]['id'] == workout.id:
                            schedule[key] = WorkoutSerializer(workout).data
                            split.save()
            
            user.workouts.add(completed_workout)
            
            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
        
@api_view(['PUT'])
def log_workout(request, id):
    if request.method == 'PUT':
        try: 
            total_volume = 0
            user = User.objects.get(pk=request.data.get('userId'))
            core_workout = Workout.objects.get(pk=id)
            date = request.data.get('completed_date')

            try:
                workout_to_delete = user.workouts.get(completed_date=date)
                exercises = workout_to_delete.exercises.all()

                for exercise in exercises:
                    sets = exercise.sets.all()
                    sets.delete()
                    exercise.delete()

                workout_to_delete.delete()
            except Workout.DoesNotExist:
                pass

            completed_workout = Workout(title=core_workout.title, completed_date=date)
            completed_workout.save()

            log_exercises = request.data.get('exercises')

            
            for exercise in core_workout.exercises.all():
                completed_exercise = Exercise(title=exercise.title, exercise_num=exercise.exercise_num)
                completed_exercise.save()
                exercise_volume = 1
                for set in exercise.sets.all():
                    completed_set = Set(set_num=set.set_num, reps=log_exercises[exercise.exercise_num-1]['sets'][set.set_num-1]['reps'], weight=log_exercises[exercise.exercise_num-1]['sets'][set.set_num-1]['weight'])
                    print(float(completed_set.weight))
                    exercise_volume += float(completed_set.reps) * float(completed_set.weight)
                    completed_set.save()
                    completed_exercise.sets.add(completed_set)
                total_volume += exercise_volume
                completed_workout.exercises.add(completed_exercise)

            completed_workout.volume = total_volume
            completed_workout.save()

            print(core_workout.volume)
            print(total_volume)

            if core_workout.volume is None or total_volume >= core_workout.volume:
                core_workout.volume = total_volume
                core_workout.save()
                for split in user.splits.all():
                    schedule = split.schedule
                    for key in schedule:
                        if schedule[key] is not None and schedule[key]['id'] == core_workout.id:
                            schedule[key] = WorkoutSerializer(core_workout).data
                            split.save()

            user.workouts.add(completed_workout)

            user.save()
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return Response({'message': 'internal server error'})
    
    
@api_view(['POST'])
def login(request):
    data = json.loads(request.body.decode('utf-8'))
    username = data.get("username")
    password = data.get("password")
    user = authenticate(request, username=username, password=password)

    if user is not None:
        serialized_user = UserSerializer(user)
        return JsonResponse({'message': 'successful login!', 'user': serialized_user.data}, status=status.HTTP_200_OK)
    elif User.objects.get(username=username) == None:
        return JsonResponse({"message": 'Username does not exist!'}, status=401)
    else:
         return JsonResponse({"message": 'invalid credentials!'}, status=401)
    
@api_view(['POST'])
def register(request):
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

        try:
            user = User.objects.create_user(username=username, password=password, first_name=name, email=email)
            user.save()

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            access_token['user'] = UserSerializer(user).data

            return Response({'message': 'success', 'access': str(access_token), 'refresh': str(refresh)}, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            return JsonResponse({'message': 'Username already exists!'})
    
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['user'] = UserSerializer(user).data

        return token
    
class MyTokenObtainPairView(TokenObtainPairView):
     serializer_class = MyTokenObtainPairSerializer