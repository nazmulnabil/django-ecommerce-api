from rest_framework import viewsets, status
from rest_framework.response import Response
from .services import create_product, get_active_products
from .serializers import ProductSerializer, ProductCreateSerializer

class ProductViewSet(viewsets.ViewSet):
    """
    ViewSet to handle Product operations.
    """
    def list(self, request):
        # We still call our Service layer!
        products = get_active_products()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def create(self, request):
        # We still call our Service layer!
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = create_product(serializer.validated_data)
            return Response({"id": product.id, "message": "Product created!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)