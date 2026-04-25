# users/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('users/me/', views.MeView.as_view(), name='me'),

    # Addresses
    path('users/me/addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('users/me/addresses/<int:address_id>/', views.AddressDetailView.as_view(), name='address-detail'),

    # Seller
    path('seller/register/', views.SellerRegisterView.as_view(), name='seller-register'),
]