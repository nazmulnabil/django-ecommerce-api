from .models import Product
from .models import Product, Category

def get_active_products():
    """
    Business Logic: Only return products that are currently for sale.
    """
    return Product.objects.filter(is_active=True).select_related('category')

def create_product(data: dict) -> Product:
    # Get the category object
    category = Category.objects.get(id=data['category_id'])
    
    # Create the product instance
    return Product.objects.create(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category=category
    )