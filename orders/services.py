from django.db import transaction
from .models import Order
from products.models import Product
from users.models import User

def place_order(user: User, product_id: int, quantity: int) -> Order:
    """
    Handles atomic order placement with row-level locking.
    
    Raises:
        ValueError: If stock is insufficient.
        Product.DoesNotExist: If product not found.
    """
    with transaction.atomic():
        product = Product.objects.select_for_update().get(id=product_id)
        
        if product.stock < quantity:
            raise ValueError("Insufficient stock")
            
        product.stock -= quantity
        product.save()
        
        total_price = product.price * quantity
        
        return Order.objects.create(
            user=user, 
            product=product, 
            quantity=quantity, 
            total_price=total_price
        )