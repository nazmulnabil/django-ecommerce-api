from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AuthViewSet

router = DefaultRouter()
# /me/ maps to UserViewSet.list()
router.register(r'me', UserViewSet, basename='user-profile') 
# /register/ maps to AuthViewSet.create()
router.register(r'register', AuthViewSet, basename='auth-register')

urlpatterns = router.urls