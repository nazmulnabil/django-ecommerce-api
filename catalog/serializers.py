from rest_framework import serializers
from .models import (
    Category, Seller, Product, ProductImage,
    AttributeKey, ProductVariant, VariantAttribute,
    Warehouse, Inventory, InventoryReservation,
)


# ── Output Serializers (read) ──────────────────────────


class CategoryOutputSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'image', 'display_order',
            'is_active', 'parent', 'children',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategoryOutputSerializer(children, many=True).data


class SellerOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'store_name', 'is_verified', 'rating', 'created_at']
        read_only_fields = fields


class ProductImageOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'order']
        read_only_fields = fields


class VariantAttributeOutputSerializer(serializers.Serializer):
    key = serializers.CharField(source='key.name')
    value = serializers.CharField()


class ProductVariantOutputSerializer(serializers.ModelSerializer):
    attributes = VariantAttributeOutputSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'sku', 'price', 'attribute_hash', 'attributes']
        read_only_fields = fields


class ProductOutputSerializer(serializers.ModelSerializer):
    min_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    primary_images = ProductImageOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'brand', 'is_active',
            'category', 'seller', 'min_price', 'primary_images',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class ProductDetailOutputSerializer(serializers.ModelSerializer):
    category = CategoryOutputSerializer(read_only=True)
    seller = SellerOutputSerializer(read_only=True)
    images = ProductImageOutputSerializer(many=True, read_only=True)
    variants = ProductVariantOutputSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'brand',
            'is_active', 'category', 'seller',
            'images', 'variants',
            'created_at', 'updated_at',
        ]
        read_only_fields = fields


class WarehouseOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'address', 'city', 'country',
            'is_active', 'created_at',
        ]
        read_only_fields = fields


class InventoryOutputSerializer(serializers.ModelSerializer):
    available = serializers.IntegerField(read_only=True)
    warehouse = WarehouseOutputSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ['id', 'variant', 'warehouse', 'quantity', 'reserved', 'available']
        read_only_fields = fields


class ReservationOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryReservation
        fields = ['id', 'idempotency_key', 'quantity', 'status', 'created_at']
        read_only_fields = fields


# ── Input Serializers (write) ──────────────────────────


class CategoryInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    parent_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    display_order = serializers.IntegerField(default=0)


class SellerInputSerializer(serializers.Serializer):
    store_name = serializers.CharField(max_length=255)


class ProductInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=500)
    description = serializers.CharField()
    category_id = serializers.IntegerField()
    brand = serializers.CharField(max_length=255, required=False, default='')


class ProductUpdateInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=500, required=False)
    description = serializers.CharField(required=False)
    brand = serializers.CharField(max_length=255, required=False)
    is_active = serializers.BooleanField(required=False)
    category_id = serializers.IntegerField(required=False)


class VariantInputSerializer(serializers.Serializer):
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    attributes = serializers.DictField(
        required=False, default=dict,
        child=serializers.CharField(max_length=255)
    )


class WarehouseInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    country = serializers.CharField(max_length=100)


class InventoryInitializeInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)


class InventoryReconcileInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)


class InventoryReserveInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    idempotency_key = serializers.CharField(max_length=255)
