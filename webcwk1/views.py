from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, logout
from django.contrib.auth import login as login_dj
from datetime import datetime
from django.utils.timezone import make_aware
import json

from .models import Author, NewsStory


# Create your views here.
def index(request):
    return HttpResponse("Index Page.")


@csrf_exempt
def login(request):
    def validate_request(request):
        if request.method != 'POST':
            return HttpResponse('Invalid request method', status=405, content_type='text/plain')
        return None

    def get_user_credentials(request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        return username, password

    def perform_authentication(request, username, password):
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_dj(request, user)
            return HttpResponse('Login successful', status=200, content_type='text/plain')
        else:
            return HttpResponse("Username or password incorrect", status=401, content_type='text/plain')

    response = validate_request(request)
    if response:
        return response
    username, password = get_user_credentials(request)
    return perform_authentication(request, username, password)


@csrf_exempt
def logout_view(request):
    def validate_request(request):
        if request.method != 'POST':
            return HttpResponse('Invalid request method', status=405, content_type='text/plain')
        return None

    def perform_logout(request):
        if request.user.is_authenticated:
            logout(request)
        return HttpResponse('Logout successful', status=200, content_type='text/plain')

    response = validate_request(request)
    if response:
        return response
    return perform_logout(request)


#  if request.user.authenticated
@csrf_exempt
def post_story(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponse('User not logged in', status=503, content_type='text/plain')
        try:
            author = request.user
            json_data = json.loads(request.body.decode('utf-8'))
            region = json_data['region']
            category = json_data['category']
            if region not in {'uk', 'eu', 'w'}:
                return HttpResponse('Invalid region', status=503, content_type='text/plain')
            if category not in {'pol', 'art', 'tech', 'trivia'}:
                return HttpResponse('Invalid category', status=503, content_type='text/plain')
            NewsStory.objects.create(
                headline=json_data['headline'],
                category=json_data['category'],
                region=json_data['region'],
                author=author,
                details=json_data['details'],
                date=datetime.now()
            )
            return HttpResponse(status=201, content_type='text/plain')
        except Exception as e:
            return HttpResponse(f'Failed to add story: {str(e)}', status=503, content_type='text/plain')

    elif request.method == 'GET':
        category = request.GET.get('story_cat', '*')
        region = request.GET.get('story_region', '*')
        date_str = request.GET.get('story_date', '*')

        date = '*'
        if date_str != '*':
            try:
                date = datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                return HttpResponse('Invalid date format. Date must be in DD/MM/YYYY format.', status=400,
                                    content_type='text/plain')

        filters = {}
        if category != '*':
            filters['category'] = category
        if region != '*':
            filters['region'] = region
        if date != '*' and date != None:
            filters['date__gte'] = date

        stories = NewsStory.objects.filter(**filters)
        if stories.exists():
            stories_list = [
                {
                    'key': str(story.pk),
                    'headline': story.headline,
                    'story_cat': story.category,
                    'story_region': story.region,
                    'author': story.author.username,
                    'story_date': story.date.strftime('%Y-%m-%d'),
                    'story_details': story.details
                } for story in stories
            ]
            return JsonResponse({'stories': stories_list})
        else:
            return HttpResponse('No stories found', status=404, content_type='text/plain')

    else:
        return HttpResponse('Invalid request method', status=405, content_type='text/plain')


@csrf_exempt
@login_required
def delete_story(request, key):
    def validate_request_method(request):
        if request.method != 'DELETE':
            return HttpResponse('Invalid request method', status=503, content_type='text/plain')
        return None

    def delete_user_story(request, key):
        try:
            story = get_object_or_404(NewsStory, pk=key, author=request.user)
            story.delete()
            return HttpResponse(status=200, content_type='text/plain')
        except NewsStory.DoesNotExist:
            return HttpResponse('Story not found', status=404, content_type='text/plain')
        except Exception as e:
            return HttpResponse(str(e), status=503, content_type='text/plain')

    response = validate_request_method(request)
    if response:
        return response
    return delete_user_story(request, key)
