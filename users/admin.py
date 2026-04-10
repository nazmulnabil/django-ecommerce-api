from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# This tells the Admin panel to use your custom User model
admin.site.register(User, UserAdmin)