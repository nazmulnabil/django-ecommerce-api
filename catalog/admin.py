from django.contrib import admin
from .models import (
    Category, Seller, Product, ProductImage,
    AttributeKey, ProductVariant, VariantAttribute,
    Warehouse, Inventory, InventoryReservation,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'display_order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'user', 'is_verified', 'rating']
    list_filter = ['is_verified']
    search_fields = ['store_name']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    extra = 0


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'price', 'attribute_hash']
    list_filter = ['product']
    search_fields = ['sku']
    inlines = [VariantAttributeInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'seller', 'category', 'brand', 'is_active']
    list_filter = ['is_active', 'category', 'seller']
    search_fields = ['name', 'slug', 'brand']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(AttributeKey)
class AttributeKeyAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'is_active']
    list_filter = ['is_active', 'country']
    search_fields = ['name', 'city']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['variant', 'warehouse', 'quantity', 'reserved', 'available']
    list_filter = ['warehouse']


@admin.register(InventoryReservation)
class InventoryReservationAdmin(admin.ModelAdmin):
    list_display = ['idempotency_key', 'inventory', 'quantity', 'status']
    list_filter = ['status']
    search_fields = ['idempotency_key']
