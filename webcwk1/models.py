from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin


class Author(AbstractUser):
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=64)

    def __str__(self):
        return self.username


class NewsStory(models.Model):
    POLITICAL = 'pol'
    ART = 'art'
    TECHNOLOGY = 'tech'
    TRIVIA = 'trivia'
    UK = 'uk'
    EUROPE = 'eu'
    WORLD = 'w'

    CATEGORY_CHOICES = [
        (POLITICAL, 'Politics'),
        (ART, 'Art'),
        (TECHNOLOGY, 'Technology'),
        (TRIVIA, 'Trivia'),
    ]

    REGION_CHOICES = [
        (UK, 'UK'),
        (EUROPE, 'Europe'),
        (WORLD, 'World'),
    ]

    headline = models.CharField(max_length=64, help_text="Enter the headline of the news story.")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, help_text="Select the category of the news story.")
    region = models.CharField(max_length=20, choices=REGION_CHOICES, help_text="Select the geographical region of the news story.")
    author = models.ForeignKey('Author', on_delete=models.CASCADE, help_text="Select the author of the news story.")
    date = models.DateTimeField(auto_now_add=True, help_text="The date and time the story was added.")
    details = models.CharField(max_length=128, help_text="Enter the details of the news story.")

    def __str__(self):
        return self.headline
