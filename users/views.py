from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer

class MeView(APIView):
    # This ensures ONLY people with a valid JWT token can see this
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 'request.user' is automatically populated by the JWT middleware!
        serializer = UserSerializer(request.user)
        return Response(serializer.data)