import pytest
from decimal import Decimal
from model_bakery import baker
from catalog.models import (
    Category, Seller, Product, ProductVariant,
    VariantAttribute, AttributeKey, Warehouse,
    Inventory, InventoryReservation, EMPTY_ATTRIBUTES_HASH
)
from catalog.services import (
    create_category,
    create_seller,
    create_product,
    update_product,
    deactivate_product,
    create_variant,
    create_warehouse,
    initialise_inventory,
    reconcile_inventory,
    reserve_inventory,
    release_reservation,
    confirm_reservation,
)
from catalog.exceptions import (
    CategoryNotFoundError,
    SellerAlreadyExistsError,
    DuplicateSkuError,
    DuplicateVariantError,
    InsufficientStockError,
    NegativeInventoryError,
    InventoryNotFoundError,
    InvalidInventoryOperationError,
)
from users.models import User

pytestmark = pytest.mark.django_db


# ── Category ──────────────────────────────────────────────────────────────────

class TestCreateCategory:

    def test_creates_category(self):
        category = create_category(name='Electronics', slug='electronics')
        assert category.id is not None
        assert category.name == 'Electronics'
        assert category.slug == 'electronics'

    def test_creates_child_category(self):
        parent = create_category(name='Electronics', slug='electronics')
        child = create_category(
            name='Phones', slug='phones', parent_id=parent.id
        )
        assert child.parent == parent

    def test_raises_if_parent_not_found(self):
        with pytest.raises(CategoryNotFoundError):
            create_category(name='Phones', slug='phones', parent_id=99999)

    def test_display_order_default_zero(self):
        category = create_category(name='Electronics', slug='electronics')
        assert category.display_order == 0

    def test_custom_display_order(self):
        category = create_category(
            name='Electronics', slug='electronics', display_order=5
        )
        assert category.display_order == 5


# ── Seller ────────────────────────────────────────────────────────────────────

class TestCreateSeller:

    def test_creates_seller(self):
        user = baker.make(User)
        seller = create_seller(user=user, store_name='Nabil Store')
        assert seller.id is not None
        assert seller.store_name == 'Nabil Store'
        assert seller.user == user

    def test_raises_if_already_seller(self):
        user = baker.make(User)
        create_seller(user=user, store_name='Nabil Store')
        with pytest.raises(SellerAlreadyExistsError):
            create_seller(user=user, store_name='Another Store')

    def test_is_verified_false_by_default(self):
        user = baker.make(User)
        seller = create_seller(user=user, store_name='Nabil Store')
        assert seller.is_verified == False


# ── Product ───────────────────────────────────────────────────────────────────

class TestCreateProduct:

    def test_creates_product(self):
        seller = baker.make(Seller)
        category = baker.make(Category, is_active=True)
        product = create_product(
            seller=seller,
            category_id=category.id,
            name='iPhone 15',
            description='Latest iPhone',
        )
        assert product.id is not None
        assert product.name == 'iPhone 15'
        assert product.seller == seller
        assert product.category == category

    def test_slug_generated_from_name(self):
        seller = baker.make(Seller)
        category = baker.make(Category, is_active=True)
        product = create_product(
            seller=seller,
            category_id=category.id,
            name='iPhone 15',
            description='Latest iPhone',
        )
        assert product.slug == 'iphone-15'

    def test_raises_if_category_not_found(self):
        seller = baker.make(Seller)
        with pytest.raises(CategoryNotFoundError):
            create_product(
                seller=seller,
                category_id=99999,
                name='iPhone 15',
                description='Latest iPhone',
            )

    def test_raises_if_category_inactive(self):
        seller = baker.make(Seller)
        category = baker.make(Category, is_active=False)
        with pytest.raises(CategoryNotFoundError):
            create_product(
                seller=seller,
                category_id=category.id,
                name='iPhone 15',
                description='Latest iPhone',
            )

    def test_slug_collision_handled(self):
        seller = baker.make(Seller)
        category = baker.make(Category, is_active=True)
        product1 = create_product(
            seller=seller,
            category_id=category.id,
            name='iPhone 15',
            description='First',
        )
        product2 = create_product(
            seller=seller,
            category_id=category.id,
            name='iPhone 15',
            description='Second',
        )
        assert product1.slug != product2.slug

    def test_is_active_by_default(self):
        seller = baker.make(Seller)
        category = baker.make(Category, is_active=True)
        product = create_product(
            seller=seller,
            category_id=category.id,
            name='iPhone 15',
            description='Latest',
        )
        assert product.is_active == True


class TestUpdateProduct:

    def test_updates_name(self):
        product = baker.make(Product)
        updated = update_product(product=product, name='New Name')
        assert updated.name == 'New Name'

    def test_updates_brand(self):
        product = baker.make(Product)
        updated = update_product(product=product, brand='Apple')
        assert updated.brand == 'Apple'

    def test_updates_is_active(self):
        product = baker.make(Product, is_active=True)
        updated = update_product(product=product, is_active=False)
        assert updated.is_active == False

    def test_only_provided_fields_updated(self):
        product = baker.make(Product, name='Original', brand='Samsung')
        updated = update_product(product=product, brand='Apple')
        assert updated.name == 'Original'
        assert updated.brand == 'Apple'

    def test_raises_if_category_not_found(self):
        product = baker.make(Product)
        with pytest.raises(CategoryNotFoundError):
            update_product(product=product, category_id=99999)


class TestDeactivateProduct:

    def test_deactivates_product(self):
        product = baker.make(Product, is_active=True)
        deactivate_product(product=product)
        product.refresh_from_db()
        assert product.is_active == False


# ── Variant ───────────────────────────────────────────────────────────────────

class TestCreateVariant:

    def test_creates_variant_with_attributes(self):
        product = baker.make(Product)
        variant = create_variant(
            product=product,
            sku='IPH15-BLK-128',
            price=Decimal('999.00'),
            attributes={'color': 'black', 'storage': '128gb'},
        )
        assert variant.id is not None
        assert variant.sku == 'IPH15-BLK-128'
        assert variant.price == Decimal('999.00')

    def test_creates_variant_attributes(self):
        product = baker.make(Product)
        variant = create_variant(
            product=product,
            sku='IPH15-BLK-128',
            price=Decimal('999.00'),
            attributes={'color': 'black', 'storage': '128gb'},
        )
        assert variant.attributes.count() == 2

    def test_attributes_normalized(self):
        product = baker.make(Product)
        variant = create_variant(
            product=product,
            sku='IPH15-BLK-128',
            price=Decimal('999.00'),
            attributes={'Color': 'BLACK', 'Storage': '128GB'},
        )
        attrs = {
            a.key.name: a.value
            for a in variant.attributes.all()
        }
        assert attrs['color'] == 'black'
        assert attrs['storage'] == '128gb'

    def test_raises_on_duplicate_sku(self):
        product = baker.make(Product)
        create_variant(
            product=product,
            sku='IPH15-BLK-128',
            price=Decimal('999.00'),
            attributes={'color': 'black'},
        )
        with pytest.raises(DuplicateSkuError):
            create_variant(
                product=product,
                sku='IPH15-BLK-128',
                price=Decimal('999.00'),
                attributes={'color': 'white'},
            )

    def test_raises_on_duplicate_attribute_combination(self):
        product = baker.make(Product)
        create_variant(
            product=product,
            sku='IPH15-BLK-128',
            price=Decimal('999.00'),
            attributes={'color': 'black', 'storage': '128gb'},
        )
        with pytest.raises(DuplicateVariantError):
            create_variant(
                product=product,
                sku='IPH15-BLK-256',
                price=Decimal('1099.00'),
                attributes={'storage': '128gb', 'color': 'black'},
            )

    def test_empty_attributes_uses_sentinel_hash(self):
        product = baker.make(Product)
        variant = create_variant(
            product=product,
            sku='IPH15-DEFAULT',
            price=Decimal('999.00'),
            attributes={},
        )
        assert variant.attribute_hash == EMPTY_ATTRIBUTES_HASH

    def test_raises_on_negative_price(self):
        product = baker.make(Product)
        with pytest.raises(ValueError):
            create_variant(
                product=product,
                sku='IPH15-BLK',
                price=Decimal('-1.00'),
                attributes={},
            )


# ── Inventory ─────────────────────────────────────────────────────────────────

class TestInitialiseInventory:

    def test_creates_inventory(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        inventory = initialise_inventory(
            variant=variant, warehouse=warehouse, quantity=100
        )
        assert inventory.quantity == 100
        assert inventory.reserved == 0

    def test_raises_if_already_exists(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        initialise_inventory(variant=variant, warehouse=warehouse, quantity=100)
        with pytest.raises(InvalidInventoryOperationError):
            initialise_inventory(
                variant=variant, warehouse=warehouse, quantity=50
            )

    def test_raises_on_negative_quantity(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        with pytest.raises(ValueError):
            initialise_inventory(
                variant=variant, warehouse=warehouse, quantity=-1
            )


class TestReconcileInventory:

    def test_updates_quantity(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        inventory = baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=0
        )
        reconcile_inventory(variant=variant, warehouse=warehouse, quantity=95)
        inventory.refresh_from_db()
        assert inventory.quantity == 95

    def test_raises_if_quantity_below_reserved(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=10
        )
        with pytest.raises(InvalidInventoryOperationError):
            reconcile_inventory(
                variant=variant, warehouse=warehouse, quantity=5
            )

    def test_raises_if_inventory_not_found(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        with pytest.raises(InventoryNotFoundError):
            reconcile_inventory(
                variant=variant, warehouse=warehouse, quantity=50
            )


class TestReserveInventory:

    def test_reserves_stock(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=0
        )
        reservation = reserve_inventory(
            variant=variant,
            warehouse=warehouse,
            quantity=2,
            idempotency_key='order_5_item_1',
        )
        assert reservation.quantity == 2
        assert reservation.status == InventoryReservation.Status.ACTIVE

    def test_inventory_reserved_incremented(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        inventory = baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=0
        )
        reserve_inventory(
            variant=variant,
            warehouse=warehouse,
            quantity=3,
            idempotency_key='order_5_item_1',
        )
        inventory.refresh_from_db()
        assert inventory.reserved == 3

    def test_idempotent_on_same_key(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=0
        )
        reserve_inventory(
            variant=variant, warehouse=warehouse,
            quantity=2, idempotency_key='order_5_item_1',
        )
        # Second call with same key
        reserve_inventory(
            variant=variant, warehouse=warehouse,
            quantity=2, idempotency_key='order_5_item_1',
        )
        # Reserved should still be 2, not 4
        inventory = Inventory.objects.get(variant=variant, warehouse=warehouse)
        assert inventory.reserved == 2

    def test_raises_on_insufficient_stock(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=5, reserved=0
        )
        with pytest.raises(InsufficientStockError):
            reserve_inventory(
                variant=variant, warehouse=warehouse,
                quantity=10, idempotency_key='order_5_item_1',
            )

    def test_raises_if_inventory_not_found(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        with pytest.raises(InventoryNotFoundError):
            reserve_inventory(
                variant=variant, warehouse=warehouse,
                quantity=1, idempotency_key='order_5_item_1',
            )


class TestReleaseReservation:

    def test_releases_reservation(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        inventory = baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=5
        )
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            quantity=5,
            status=InventoryReservation.Status.ACTIVE,
        )
        release_reservation(reservation=reservation)
        inventory.refresh_from_db()
        reservation.refresh_from_db()
        assert inventory.reserved == 0
        assert reservation.status == InventoryReservation.Status.RELEASED

    def test_raises_if_not_active(self):
        inventory = baker.make(Inventory, quantity=10, reserved=0)
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            quantity=1,
            status=InventoryReservation.Status.CONFIRMED,
        )
        with pytest.raises(InvalidInventoryOperationError):
            release_reservation(reservation=reservation)


class TestConfirmReservation:

    def test_confirms_reservation(self):
        variant = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        inventory = baker.make(
            Inventory, variant=variant, warehouse=warehouse,
            quantity=100, reserved=5
        )
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            quantity=5,
            status=InventoryReservation.Status.ACTIVE,
        )
        confirm_reservation(reservation=reservation)
        inventory.refresh_from_db()
        reservation.refresh_from_db()
        assert inventory.quantity == 95
        assert inventory.reserved == 0
        assert reservation.status == InventoryReservation.Status.CONFIRMED

    def test_raises_if_not_active(self):
        inventory = baker.make(Inventory, quantity=10, reserved=0)
        reservation = baker.make(
            InventoryReservation,
            inventory=inventory,
            quantity=1,
            status=InventoryReservation.Status.RELEASED,
        )
        with pytest.raises(InvalidInventoryOperationError):
            confirm_reservation(reservation=reservation)