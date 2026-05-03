import hashlib
import uuid
from decimal import Decimal
from django.db import transaction, IntegrityError
from django.utils.text import slugify

from users.models import User
from .models import (
    Category, Seller, Product,
    AttributeKey, ProductVariant, VariantAttribute,
    Warehouse, Inventory, InventoryReservation,
    EMPTY_ATTRIBUTES_HASH,
)
from .exceptions import (
    CategoryNotFoundError,
    SellerAlreadyExistsError,
    DuplicateSkuError,
    DuplicateVariantError,
    InsufficientStockError,
    NegativeInventoryError,
    InventoryNotFoundError,
    InvalidInventoryOperationError,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_attributes(attributes: dict) -> dict:
    return {
        k.strip().lower(): v.strip().lower()
        for k, v in attributes.items()
    }


def _compute_attribute_hash(normalized: dict) -> str:
    if not normalized:
        return EMPTY_ATTRIBUTES_HASH
    pairs = sorted(normalized.items())
    raw = "&".join(f"{k}={v}" for k, v in pairs)
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_locked_inventory(
    *,
    variant: ProductVariant,
    warehouse: Warehouse,
) -> Inventory:
    try:
        return (
            Inventory.objects
            .select_for_update()
            .get(variant=variant, warehouse=warehouse)
        )
    except Inventory.DoesNotExist:
        raise InventoryNotFoundError(
            f"No inventory for '{variant.sku}' "
            f"in '{warehouse.name}'."
        )


# ── Category ──────────────────────────────────────────────────────────────────

def create_category(
    *,
    name: str,
    slug: str,
    parent_id: int | None = None,
    display_order: int = 0,
) -> Category:
    parent = None
    if parent_id is not None:
        try:
            parent = Category.objects.get(id=parent_id)
        except Category.DoesNotExist:
            raise CategoryNotFoundError(
                f"Parent category {parent_id} not found."
            )
    return Category.objects.create(
        name=name,
        slug=slug,
        parent=parent,
        display_order=display_order,
    )


# ── Seller ────────────────────────────────────────────────────────────────────

def create_seller(*, user: User, store_name: str) -> Seller:
    if Seller.objects.filter(user=user).exists():
        raise SellerAlreadyExistsError(
            f"User {user.email} already has a seller profile."
        )
    return Seller.objects.create(user=user, store_name=store_name)


# ── Product ───────────────────────────────────────────────────────────────────

def create_product(
    *,
    seller: Seller,
    category_id: int,
    name: str,
    description: str,
    brand: str = '',
) -> Product:
    try:
        category = Category.objects.get(id=category_id, is_active=True)
    except Category.DoesNotExist:
        raise CategoryNotFoundError(
            f"Active category {category_id} not found."
        )

    for attempt in range(5):
        slug = (
            slugify(name)
            if attempt == 0
            else f"{slugify(name)}-{uuid.uuid4().hex[:6]}"
        )
        try:
            return Product.objects.create(
                seller=seller,
                category=category,
                name=name,
                slug=slug,
                description=description,
                brand=brand,
            )
        except IntegrityError:
            if attempt == 4:
                raise
            continue


def update_product(
    *,
    product: Product,
    name: str | None = None,
    description: str | None = None,
    brand: str | None = None,
    is_active: bool | None = None,
    category_id: int | None = None,
) -> Product:
    update_fields = []
    if name is not None:
        product.name = name
        update_fields.append('name')
    if description is not None:
        product.description = description
        update_fields.append('description')
    if brand is not None:
        product.brand = brand
        update_fields.append('brand')
    if is_active is not None:
        product.is_active = is_active
        update_fields.append('is_active')
    if category_id is not None:
        try:
            product.category = Category.objects.get(
                id=category_id, is_active=True
            )
            update_fields.append('category')
        except Category.DoesNotExist:
            raise CategoryNotFoundError(
                f"Active category {category_id} not found."
            )
    if update_fields:
        product.save(update_fields=update_fields)
    return product


def deactivate_product(*, product: Product) -> None:
    product.is_active = False
    product.save(update_fields=['is_active'])


# ── Variant ───────────────────────────────────────────────────────────────────

def create_variant(
    *,
    product: Product,
    sku: str,
    price: Decimal,
    attributes: dict | None = None,
) -> ProductVariant:
    if price < 0:
        raise ValueError("Price cannot be negative.")

    normalized = _normalize_attributes(attributes or {})
    attribute_hash = _compute_attribute_hash(normalized)

    with transaction.atomic():
        try:
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                price=price,
                attribute_hash=attribute_hash,
            )
        except IntegrityError as e:
            error = str(e)
            if 'unique_variant_per_product' in error:
                raise DuplicateVariantError(
                    f"A variant with this attribute combination "
                    f"already exists for '{product.name}'."
                )
            if 'sku' in error:
                raise DuplicateSkuError(f"SKU '{sku}' is already in use.")
            raise

        for key_name, value in normalized.items():
            key, _ = AttributeKey.objects.get_or_create(name=key_name)
            VariantAttribute.objects.create(
                variant=variant,
                key=key,
                value=value,
            )

    return variant


# ── Warehouse ─────────────────────────────────────────────────────────────────

def create_warehouse(
    *,
    name: str,
    address: str,
    city: str,
    country: str,
) -> Warehouse:
    return Warehouse.objects.create(
        name=name,
        address=address,
        city=city,
        country=country,
    )


# ── Inventory ─────────────────────────────────────────────────────────────────

def initialise_inventory(
    *,
    variant: ProductVariant,
    warehouse: Warehouse,
    quantity: int,
) -> Inventory:
    if quantity < 0:
        raise ValueError("Initial quantity cannot be negative.")
    try:
        return Inventory.objects.create(
            variant=variant,
            warehouse=warehouse,
            quantity=quantity,
            reserved=0,
        )
    except IntegrityError:
        raise InvalidInventoryOperationError(
            f"Inventory for '{variant.sku}' in "
            f"'{warehouse.name}' already exists. "
            f"Use reconcile_inventory to adjust."
        )


def reconcile_inventory(
    *,
    variant: ProductVariant,
    warehouse: Warehouse,
    quantity: int,
) -> Inventory:
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    with transaction.atomic():
        inventory = _get_locked_inventory(
            variant=variant, warehouse=warehouse
        )
        if quantity < inventory.reserved:
            raise InvalidInventoryOperationError(
                f"Cannot set quantity to {quantity} — "
                f"{inventory.reserved} units are reserved."
            )
        inventory.quantity = quantity
        inventory.save(update_fields=['quantity'])
        return inventory


def reserve_inventory(
    *,
    variant: ProductVariant,
    warehouse: Warehouse,
    quantity: int,
    idempotency_key: str,
) -> InventoryReservation:
    if quantity <= 0:
        raise ValueError("Reserve quantity must be positive.")

    with transaction.atomic():
        existing = InventoryReservation.objects.filter(
            idempotency_key=idempotency_key
        ).first()
        if existing:
            return existing

        inventory = _get_locked_inventory(
            variant=variant, warehouse=warehouse
        )

        if inventory.available < quantity:
            raise InsufficientStockError(
                f"Only {inventory.available} units available "
                f"for '{variant.sku}'."
            )

        inventory.reserved += quantity
        inventory.save(update_fields=['reserved'])

        try:
            return InventoryReservation.objects.create(
                inventory=inventory,
                idempotency_key=idempotency_key,
                quantity=quantity,
            )
        except IntegrityError:
            inventory.reserved -= quantity
            inventory.save(update_fields=['reserved'])
            return InventoryReservation.objects.get(
                idempotency_key=idempotency_key
            )


def release_reservation(
    *,
    reservation: InventoryReservation,
) -> None:
    if reservation.status != InventoryReservation.Status.ACTIVE:
        raise InvalidInventoryOperationError(
            f"Only ACTIVE reservations can be released. "
            f"Current status: '{reservation.status}'."
        )
    with transaction.atomic():
        inventory = _get_locked_inventory(
            variant=reservation.inventory.variant,
            warehouse=reservation.inventory.warehouse,
        )
        inventory.reserved -= reservation.quantity
        inventory.save(update_fields=['reserved'])
        reservation.status = InventoryReservation.Status.RELEASED
        reservation.save(update_fields=['status'])


def confirm_reservation(
    *,
    reservation: InventoryReservation,
) -> None:
    if reservation.status != InventoryReservation.Status.ACTIVE:
        raise InvalidInventoryOperationError(
            f"Only ACTIVE reservations can be confirmed. "
            f"Current status: '{reservation.status}'."
        )
    with transaction.atomic():
        inventory = _get_locked_inventory(
            variant=reservation.inventory.variant,
            warehouse=reservation.inventory.warehouse,
        )
        if inventory.quantity < reservation.quantity:
            raise NegativeInventoryError(
                f"Cannot confirm {reservation.quantity} — "
                f"only {inventory.quantity} in stock."
            )
        inventory.quantity -= reservation.quantity
        inventory.reserved -= reservation.quantity
        inventory.save(update_fields=['quantity', 'reserved'])
        reservation.status = InventoryReservation.Status.CONFIRMED
        reservation.save(update_fields=['status'])