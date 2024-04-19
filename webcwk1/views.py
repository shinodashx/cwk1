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
    def handle_post_request(request):
        if not request.user.is_authenticated:
            return HttpResponse('User not logged in', status=401, content_type='text/plain')

        author = get_object_or_404(Author, pk=request.user.id)
        json_data = json.loads(request.body.decode('utf-8'))
        NewsStory.objects.create(
            headline=json_data.get('headline'),
            category=json_data.get('category'),
            region=json_data.get('region'),
            author=author,
            details=json_data.get('details'),
            date=datetime.now()
        )
        return HttpResponse(status=201, content_type='text/plain')

    def handle_get_request(request):
        filters = {
            'category': request.GET.get('story_cat', None),
            'region': request.GET.get('story_region', None),
            'date__gte': parse_date(request.GET.get('story_date'))
        }
        filters = {key: value for key, value in filters.items() if value is not None}

        stories = NewsStory.objects.filter(**filters)
        if stories:
            return JsonResponse({'stories': [format_story(story) for story in stories]})
        else:
            return HttpResponse('No stories found', status=404, content_type='text/plain')

    def parse_date(date_str):
        if date_str and date_str != '*':
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').date()
            except ValueError:
                HttpResponse('Invalid date format. Date must be in DD/MM/YYYY format.', status=400)
        return None

    def format_story(story):
        return {
            'key': str(story.pk),
            'headline': story.headline,
            'story_cat': story.category,
            'story_region': story.region,
            'author': story.author.name,
            'story_date': story.date.strftime('%Y-%m-%d'),
            'story_details': story.details
        }

    if request.method == 'POST':
        return handle_post_request(request)
    elif request.method == 'GET':
        return handle_get_request(request)
    else:
        return HttpResponse('Invalid request method', status=405, content_type='text/plain')



@csrf_exempt
@login_required
def delete_story(request, key):
    def validate_request_method(request):
        if request.method != 'DELETE':
            return HttpResponse('Invalid request method', status=405, content_type='text/plain')
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
