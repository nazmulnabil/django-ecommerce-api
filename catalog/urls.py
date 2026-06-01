from django.urls import path
from . import views

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Sellers
    path('sellers/', views.SellerCreateView.as_view(), name='seller-create'),
    path('sellers/<int:seller_id>/products/', views.SellerProductsView.as_view(), name='seller-products'),

    # Products
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<slug:slug>/deactivate/', views.ProductDeactivateView.as_view(), name='product-deactivate'),
    path('products/<slug:slug>/variants/', views.ProductVariantCreateView.as_view(), name='product-variant-create'),

    # Warehouses
    path('warehouses/', views.WarehouseCreateView.as_view(), name='warehouse-create'),

    # Inventory
    path('inventory/variants/<int:variant_id>/', views.InventoryByVariantView.as_view(), name='inventory-by-variant'),
    path('inventory/initialize/', views.InventoryInitializeView.as_view(), name='inventory-initialize'),
    path('inventory/reconcile/', views.InventoryReconcileView.as_view(), name='inventory-reconcile'),
    path('inventory/reserve/', views.InventoryReserveView.as_view(), name='inventory-reserve'),
    path('inventory/reservations/<int:reservation_id>/release/', views.ReservationReleaseView.as_view(), name='reservation-release'),
    path('inventory/reservations/<int:reservation_id>/confirm/', views.ReservationConfirmView.as_view(), name='reservation-confirm'),
]
