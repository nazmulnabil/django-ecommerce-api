from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    # This automatically includes the category name
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category_name', 'image']
        from rest_framework import serializers


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_id = serializers.IntegerField()
    image = serializers.ImageField(required=False)
    
    # validate() is a special method called by .is_valid()
    def validate(self, data):
        if data['price'] < 0:
            raise serializers.ValidationError({"price": "Price cannot be negative."})
        return data