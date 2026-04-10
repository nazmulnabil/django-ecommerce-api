from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # We make email unique so two people can't register with the same email
    email = models.EmailField(unique=True)
    
    # We can add extra fields here that aren't in default Django
    bio = models.TextField(blank=True, null=True)

    # This tells Django to use the Email field to log in instead of a Username
    USERNAME_FIELD = 'email'
    
    # Django usually requires 'email' in REQUIRED_FIELDS, but since it's the 
    # USERNAME_FIELD, we only need to list 'username' here for the admin panel.
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email