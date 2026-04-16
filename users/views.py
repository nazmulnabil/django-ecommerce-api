from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_user_profile_domain
from .serializers import UserProfileSerializer
from .services import register_user
from .serializers import UserRegistrationSerializer
from .serializers import UserProfileSerializer

class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user_data = get_user_profile_domain(request.user)
        serializer = UserProfileSerializer(user_data)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    # Public view, no auth needed
    permission_classes = [] 

    def create(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = register_user(serializer.validated_data)
            return Response({"id": user.id, "message": "User registered!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)