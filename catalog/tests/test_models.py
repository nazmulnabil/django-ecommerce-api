import pytest
from model_bakery import baker
from catalog.models import (
    Category, Seller, Product, ProductVariant,
    VariantAttribute, AttributeKey, Warehouse,
    Inventory, InventoryReservation, EMPTY_ATTRIBUTES_HASH
)

pytestmark = pytest.mark.django_db


class TestCategoryModel:

    def test_str_returns_name(self):
        category = baker.make(Category, name='Electronics')
        assert str(category) == 'Electronics'

    def test_slug_is_unique(self):
        baker.make(Category, slug='electronics')
        with pytest.raises(Exception):
            baker.make(Category, slug='electronics')

    def test_parent_can_be_null(self):
        category = baker.make(Category, parent=None)
        assert category.parent is None

    def test_child_links_to_parent(self):
        parent = baker.make(Category)
        child = baker.make(Category, parent=parent)
        assert child.parent == parent

    def test_is_active_default_true(self):
        category = baker.make(Category)
        assert category.is_active == True

    def test_display_order_default_zero(self):
        category = baker.make(Category)
        assert category.display_order == 0

    def test_has_created_at(self):
        category = baker.make(Category)
        assert category.created_at is not None


class TestSellerModel:

    def test_str_returns_store_name(self):
        seller = baker.make(Seller, store_name='Nabil Store')
        assert str(seller) == 'Nabil Store'

    def test_is_verified_default_false(self):
        seller = baker.make(Seller)
        assert seller.is_verified == False

    def test_rating_default(self):
        seller = baker.make(Seller)
        assert float(seller.rating) == 0.0

    def test_one_seller_per_user(self):
        from users.models import User
        user = baker.make(User)
        baker.make(Seller, user=user)
        with pytest.raises(Exception):
            baker.make(Seller, user=user)


class TestProductModel:

    def test_str_returns_name(self):
        product = baker.make(Product, name='iPhone 15')
        assert str(product) == 'iPhone 15'

    def test_slug_is_unique(self):
        baker.make(Product, slug='iphone-15')
        with pytest.raises(Exception):
            baker.make(Product, slug='iphone-15')

    def test_is_active_default_true(self):
        product = baker.make(Product)
        assert product.is_active == True

    def test_product_links_to_seller(self):
        seller = baker.make(Seller)
        product = baker.make(Product, seller=seller)
        assert product.seller == seller

    def test_product_links_to_category(self):
        category = baker.make(Category)
        product = baker.make(Product, category=category)
        assert product.category == category


class TestProductVariantModel:

    def test_str_returns_product_and_sku(self):
        product = baker.make(Product, name='iPhone 15')
        variant = baker.make(ProductVariant, product=product, sku='IPH-BLK')
        assert str(variant) == 'iPhone 15 — IPH-BLK'

    def test_sku_is_unique(self):
        baker.make(ProductVariant, sku='IPH-BLK')
        with pytest.raises(Exception):
            baker.make(ProductVariant, sku='IPH-BLK')

    def test_attribute_hash_stored(self):
        variant = baker.make(ProductVariant, attribute_hash='abc123')
        assert variant.attribute_hash == 'abc123'

    def test_duplicate_attribute_hash_per_product_rejected(self):
        product = baker.make(Product)
        baker.make(ProductVariant, product=product, attribute_hash='abc123')
        with pytest.raises(Exception):
            baker.make(ProductVariant, product=product, attribute_hash='abc123')

    def test_same_hash_different_products_allowed(self):
        product1 = baker.make(Product)
        product2 = baker.make(Product)
        baker.make(ProductVariant, product=product1, attribute_hash='abc123')
        variant2 = baker.make(ProductVariant, product=product2, attribute_hash='abc123')
        assert variant2.id is not None


class TestAttributeKeyModel:

    def test_name_saved_lowercase(self):
        key = baker.make(AttributeKey, name='Color')
        assert key.name == 'color'

    def test_name_stripped(self):
        key = baker.make(AttributeKey, name='  size  ')
        assert key.name == 'size'


class TestInventoryModel:

    def test_available_property(self):
        inventory = baker.make(Inventory, quantity=10, reserved=3)
        assert inventory.available == 7

    def test_available_when_nothing_reserved(self):
        inventory = baker.make(Inventory, quantity=5, reserved=0)
        assert inventory.available == 5

    def test_unique_variant_warehouse(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(Inventory, variant=variant, warehouse=warehouse)
        with pytest.raises(Exception):
            baker.make(Inventory, variant=variant, warehouse=warehouse)

    def test_str_returns_sku_and_warehouse(self):
        variant = baker.make(ProductVariant, sku='SKU-001')
        warehouse = baker.make(Warehouse, name='Dhaka WH')
        inventory = baker.make(
            Inventory, variant=variant, warehouse=warehouse
        )
        assert str(inventory) == 'SKU-001 @ Dhaka WH'

    def test_reserved_cannot_exceed_quantity(self):
        from django.db import IntegrityError
        with pytest.raises(Exception):
            baker.make(Inventory, quantity=5, reserved=10)


class TestInventoryReservationModel:

    def test_str_returns_key_quantity_status(self):
        inventory = baker.make(Inventory, quantity=10, reserved=0)
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            idempotency_key='order_5_item_1',
            quantity=2,
            status=InventoryReservation.Status.ACTIVE
        )
        assert 'order_5_item_1' in str(reservation)
        assert '2' in str(reservation)
        assert 'active' in str(reservation)

    def test_idempotency_key_is_unique(self):
        inventory = baker.make(Inventory, quantity=10, reserved=0)
        baker.make(
            InventoryReservation,
            inventory=inventory,
            idempotency_key='order_5_item_1',
            quantity=1
        )
        with pytest.raises(Exception):
            baker.make(
                InventoryReservation,
                inventory=inventory,
                idempotency_key='order_5_item_1',
                quantity=1
            )

    def test_default_status_is_active(self):
        inventory = baker.make(Inventory, quantity=10, reserved=0)
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            quantity=1
        )
        assert reservation.status == InventoryReservation.Status.ACTIVE