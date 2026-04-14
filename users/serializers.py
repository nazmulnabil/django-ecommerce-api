from rest_framework import serializers

class UserProfileSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    email_address = serializers.EmailField()
    full_username = serializers.CharField()
    bio = serializers.CharField(allow_null=True)