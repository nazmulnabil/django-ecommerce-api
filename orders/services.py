from django.db import transaction
from .models import Order
from products.models import Product

def place_order(user, product_id: int, quantity: int) -> Order:
    with transaction.atomic():
        # This locks the row in the DB so no other request can change it 
        # until this transaction finishes.
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