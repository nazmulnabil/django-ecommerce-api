from rest_framework import serializers
from .models import User 
class UserProfileSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    email_address = serializers.EmailField()
    full_username = serializers.CharField()
    bio = serializers.CharField(allow_null=True)



class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    bio = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        # We can add custom password rules here (e.g., length > 8)
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value