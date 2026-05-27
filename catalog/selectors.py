from decimal import Decimal
from django.db.models import (
    Min, Sum, F, Value,
    QuerySet, Prefetch,
    ExpressionWrapper, IntegerField,
)
from django.db.models.functions import Coalesce

from .models import (
    Category, Product, ProductVariant,
    ProductImage, Inventory,
)
from .exceptions import CategoryNotFoundError, ProductNotFoundError


_PRODUCT_ORDERING = {
    'price':       'min_price',
    '-price':      '-min_price',
    'created_at':  'created_at',
    '-created_at': '-created_at',
    'name':        'name',
    '-name':       '-name',
}
_DEFAULT_ORDERING = '-created_at'


def get_active_categories() -> QuerySet:
    return (
        Category.objects
        .filter(is_active=True)
        .order_by('display_order')
    )


def get_category_by_slug(*, slug: str) -> Category:
    try:
        return Category.objects.get(slug=slug, is_active=True)
    except Category.DoesNotExist:
        raise CategoryNotFoundError(f"Category '{slug}' not found.")


def get_products(
    *,
    category_slug: str | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    search: str | None = None,
    ordering: str = _DEFAULT_ORDERING,
    in_stock_only: bool = True,
) -> QuerySet:
    """
    Returns unsliced QuerySet.
    Pagination is handled by DRF PageNumberPagination in the view.
    avg_rating will be added when reviews domain is built.
    """
    safe_ordering = _PRODUCT_ORDERING.get(ordering, _DEFAULT_ORDERING)

    qs = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'seller')
        .prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(
                    is_primary=True
                ).only('id', 'image', 'product_id'),
                to_attr='primary_images'
            ),
            Prefetch(
                'variants',
                queryset=ProductVariant.objects
                .only('id', 'sku', 'price', 'product_id')
                .order_by('price'),
                to_attr='sorted_variants'
            )
        )
        .annotate(
            min_price=Min('variants__price'),
            total_available=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('variants__inventory_records__quantity') -
                        F('variants__inventory_records__reserved'),
                        output_field=IntegerField()
                    )
                ),
                Value(0),
                output_field=IntegerField()
            ),
        )
    )

    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if brand:
        qs = qs.filter(brand__icontains=brand)
    if min_price is not None:
        qs = qs.filter(min_price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(min_price__lte=max_price)
    if search:
        qs = qs.filter(name__icontains=search)
    if in_stock_only:
        qs = qs.filter(total_available__gt=0)

    return qs.order_by(safe_ordering)


def get_product_by_slug(*, slug: str) -> Product:
    try:
        return (
            Product.objects
            .select_related('category', 'seller')
            .prefetch_related(
                Prefetch(
                    'images',
                    queryset=ProductImage.objects.order_by('order')
                ),
                Prefetch(
                    'variants',
                    queryset=ProductVariant.objects
                    .prefetch_related('attributes__key')
                    .order_by('price')
                )
            )
            .get(slug=slug, is_active=True)
        )
    except Product.DoesNotExist:
        raise ProductNotFoundError(f"Product '{slug}' not found.")


def get_products_by_seller(*, seller_id: int) -> QuerySet:
    """Returns unsliced QuerySet. Caller paginates."""
    return (
        Product.objects
        .filter(seller_id=seller_id, is_active=True)
        .select_related('category')
        .prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_primary=True),
                to_attr='primary_images'
            )
        )
        .annotate(min_price=Min('variants__price'))
        .order_by('-created_at')
    )


def get_inventory_for_variant(*, variant: ProductVariant) -> QuerySet:
    return (
        Inventory.objects
        .filter(variant=variant)
        .select_related('warehouse')
    )