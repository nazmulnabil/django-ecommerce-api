from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
# This registers the ViewSet. Django will now create URLs like:
# /products/ (GET) -> list
# /products/ (POST) -> create
router.register(r'', ProductViewSet, basename='product')

urlpatterns = router.urls