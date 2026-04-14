from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    # This automatically includes the category name
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category_name']