from rest_framework.views import APIView
from rest_framework.response import Response
from .services import get_active_products
from .serializers import ProductSerializer

class ProductListView(APIView):
    def get(self, request):
        # 1. Fetch from Service Layer
        products = get_active_products()
        
        # 2. Serialize (Map to JSON)
        serializer = ProductSerializer(products, many=True)
        
        # 3. Return Response
        return Response(serializer.data)