import pytest
from decimal import Decimal
from model_bakery import baker
from catalog.models import (
    Category, Seller, Product, ProductVariant,
    ProductImage, Inventory, Warehouse
)
from catalog.selectors import (
    get_active_categories,
    get_category_by_slug,
    get_products,
    get_product_by_slug,
    get_products_by_seller,
    get_inventory_for_variant,
)
from catalog.exceptions import CategoryNotFoundError, ProductNotFoundError

pytestmark = pytest.mark.django_db


class TestGetActiveCategories:

    def test_returns_only_active(self):
        baker.make(Category, is_active=True, _quantity=3)
        baker.make(Category, is_active=False, _quantity=2)
        result = get_active_categories()
        assert result.count() == 3

    def test_ordered_by_display_order(self):
        baker.make(Category, is_active=True, display_order=3)
        baker.make(Category, is_active=True, display_order=1)
        baker.make(Category, is_active=True, display_order=2)
        result = list(get_active_categories())
        assert result[0].display_order == 1
        assert result[1].display_order == 2
        assert result[2].display_order == 3

    def test_returns_empty_when_none_active(self):
        baker.make(Category, is_active=False, _quantity=3)
        result = get_active_categories()
        assert result.count() == 0


class TestGetCategoryBySlug:

    def test_returns_category(self):
        baker.make(Category, slug='electronics', is_active=True)
        result = get_category_by_slug(slug='electronics')
        assert result.slug == 'electronics'

    def test_raises_if_not_found(self):
        with pytest.raises(CategoryNotFoundError):
            get_category_by_slug(slug='nonexistent')

    def test_raises_if_inactive(self):
        baker.make(Category, slug='electronics', is_active=False)
        with pytest.raises(CategoryNotFoundError):
            get_category_by_slug(slug='electronics')


class TestGetProducts:

    def test_returns_only_active_products(self):
        baker.make(Product, is_active=True, _quantity=3)
        baker.make(Product, is_active=False, _quantity=2)
        result = get_products(in_stock_only=False)
        assert result.count() == 3

    def test_filters_by_category_slug(self):
        category = baker.make(Category, slug='phones', is_active=True)
        baker.make(Product, category=category, is_active=True, _quantity=2)
        baker.make(Product, is_active=True, _quantity=3)
        result = get_products(category_slug='phones', in_stock_only=False)
        assert result.count() == 2

    def test_filters_by_brand(self):
        baker.make(Product, brand='Apple', is_active=True, _quantity=2)
        baker.make(Product, brand='Samsung', is_active=True, _quantity=3)
        result = get_products(brand='Apple', in_stock_only=False)
        assert result.count() == 2

    def test_filters_by_search(self):
        baker.make(Product, name='iPhone 15', is_active=True)
        baker.make(Product, name='Samsung Galaxy', is_active=True)
        result = get_products(search='iphone', in_stock_only=False)
        assert result.count() == 1

    def test_filters_in_stock_only(self):
        # Products with variants that have stock
        product_with_stock = baker.make(Product, is_active=True)
        variant_with_stock = baker.make(
            ProductVariant,
            product=product_with_stock,
            attribute_hash='hash-with-stock'
        )
        warehouse = baker.make(Warehouse)
        baker.make(
            Inventory,
            variant=variant_with_stock,
            warehouse=warehouse,
            quantity=10, reserved=0
        )
        # Product with variants but no stock
        product_no_stock = baker.make(Product, is_active=True)
        variant_no_stock = baker.make(
            ProductVariant,
            product=product_no_stock,
            attribute_hash='hash-no-stock'
        )
        baker.make(
            Inventory,
            variant=variant_no_stock,
            warehouse=warehouse,
            quantity=0, reserved=0
        )
        result = get_products(in_stock_only=True)
        product_ids = list(result.values_list('id', flat=True))
        assert product_with_stock.id in product_ids
        assert product_no_stock.id not in product_ids

    def test_returns_queryset(self):
        from django.db.models import QuerySet
        result = get_products()
        assert isinstance(result, QuerySet)


class TestGetProductBySlug:

    def test_returns_product(self):
        baker.make(Product, slug='iphone-15', is_active=True)
        result = get_product_by_slug(slug='iphone-15')
        assert result.slug == 'iphone-15'

    def test_raises_if_not_found(self):
        with pytest.raises(ProductNotFoundError):
            get_product_by_slug(slug='nonexistent')

    def test_raises_if_inactive(self):
        baker.make(Product, slug='iphone-15', is_active=False)
        with pytest.raises(ProductNotFoundError):
            get_product_by_slug(slug='iphone-15')

    def test_prefetches_images(self):
        product = baker.make(Product, slug='iphone-15', is_active=True)
        baker.make(ProductImage, product=product, _quantity=3)
        result = get_product_by_slug(slug='iphone-15')
        assert len(result.images.all()) == 3

    def test_prefetches_variants(self):
        product = baker.make(Product, slug='iphone-15', is_active=True)
        # Provide distinct hashes — UniqueConstraint(product, attribute_hash)
        baker.make(ProductVariant, product=product, attribute_hash='hash-001')
        baker.make(ProductVariant, product=product, attribute_hash='hash-002')
        result = get_product_by_slug(slug='iphone-15')
        assert len(result.variants.all()) == 2


class TestGetProductsBySeller:

    def test_returns_sellers_products(self):
        seller = baker.make(Seller)
        baker.make(Product, seller=seller, is_active=True, _quantity=3)
        baker.make(Product, is_active=True, _quantity=2)
        result = get_products_by_seller(seller_id=seller.id)
        assert result.count() == 3

    def test_excludes_inactive(self):
        seller = baker.make(Seller)
        baker.make(Product, seller=seller, is_active=True, _quantity=2)
        baker.make(Product, seller=seller, is_active=False, _quantity=1)
        result = get_products_by_seller(seller_id=seller.id)
        assert result.count() == 2

    def test_returns_empty_for_unknown_seller(self):
        result = get_products_by_seller(seller_id=99999)
        assert result.count() == 0


class TestGetInventoryForVariant:

    def test_returns_inventory_records(self):
        variant = baker.make(ProductVariant)
        warehouse1 = baker.make(Warehouse)
        warehouse2 = baker.make(Warehouse)
        baker.make(Inventory, variant=variant, warehouse=warehouse1)
        baker.make(Inventory, variant=variant, warehouse=warehouse2)
        result = get_inventory_for_variant(variant=variant)
        assert result.count() == 2

    def test_returns_only_variants_inventory(self):
        variant1 = baker.make(ProductVariant)
        variant2 = baker.make(ProductVariant)
        warehouse = baker.make(Warehouse)
        baker.make(Inventory, variant=variant1, warehouse=warehouse)
        result = get_inventory_for_variant(variant=variant2)
        assert result.count() == 0