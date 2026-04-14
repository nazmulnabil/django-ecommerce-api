from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import get_user_profile_domain
from .serializers import UserProfileSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_data = get_user_profile_domain(request.user)
        
        serializer = UserProfileSerializer(user_data)
        
        return Response(serializer.data)