from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.functions import Lower
from core.models import TimeStampedModel
from users.models import User
import hashlib


EMPTY_ATTRIBUTES_HASH = hashlib.sha256(b'__empty__').hexdigest()


class Category(TimeStampedModel):
    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='children'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order']
        indexes = [
            models.Index(
                fields=['display_order'],
                condition=models.Q(is_active=True),
                name='idx_category_active_order'
            ),
        ]

    def __str__(self):
        return self.name


class Seller(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )
    store_name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return self.store_name


class Product(TimeStampedModel):
    seller = models.ForeignKey(
        Seller,
        on_delete=models.PROTECT,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    name = models.CharField(max_length=500)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    brand = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['category'],
                condition=models.Q(is_active=True),
                name='idx_product_active_category'
            ),
            models.Index(
                fields=['seller'],
                condition=models.Q(is_active=True),
                name='idx_product_active_seller'
            ),
            models.Index(
                fields=['brand'],
                condition=models.Q(is_active=True),
                name='idx_product_active_brand'
            ),
        ]

    def __str__(self):
        return self.name


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"


class AttributeKey(TimeStampedModel):
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='unique_attributekey_name_ci'
            )
        ]

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    attribute_hash = models.CharField(
    max_length=64,
    default=EMPTY_ATTRIBUTES_HASH
)

    class Meta:
        ordering = ['price']
        indexes = [
            models.Index(fields=['product', 'price']),
            models.Index(
                fields=['product', 'attribute_hash'],
                name='idx_variant_product_hash'
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'attribute_hash'],
                name='unique_variant_per_product'
            )
        ]

    def __str__(self):
        return f"{self.product.name} — {self.sku}"


class VariantAttribute(TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    key = models.ForeignKey(
        AttributeKey,
        on_delete=models.PROTECT,
        related_name='values'
    )
    value = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['variant', 'key'],
                name='unique_attribute_per_variant'
            )
        ]

    def __str__(self):
        return f"{self.key.name}: {self.value}"


class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Inventory(TimeStampedModel):
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='inventory_records'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='inventory_records'
    )
    quantity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    reserved = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:                                          # ← inside Inventory
        constraints = [
            models.UniqueConstraint(
                fields=['variant', 'warehouse'],
                name='unique_inventory_per_location'
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=models.F('reserved')),
                name='inventory_reserved_lte_quantity'
            )
        ]

    @property                                           # ← inside Inventory
    def available(self) -> int:
        return self.quantity - self.reserved

    def __str__(self):                                  # ← inside Inventory
        return f"{self.variant.sku} @ {self.warehouse.name}"


class InventoryReservation(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active'
        RELEASED = 'released'
        CONFIRMED = 'confirmed'

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        related_name='reservations'
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        indexes = [
            models.Index(fields=['inventory', 'status']),
        ]

    def __str__(self):
        return (
            f"{self.idempotency_key} — "
            f"{self.quantity} units ({self.status})"
        )