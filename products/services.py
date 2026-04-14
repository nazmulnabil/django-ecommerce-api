from .models import Product

def get_active_products():
    """
    Business Logic: Only return products that are currently for sale.
    """
    return Product.objects.filter(is_active=True).select_related('category')