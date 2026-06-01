import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from model_bakery import baker

from users.models import User
from catalog.models import (
    Category, Seller, Product, ProductImage,
    ProductVariant, VariantAttribute, AttributeKey,
    Warehouse, Inventory, InventoryReservation,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return baker.make(User, email='test@example.com', username='testuser')


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def category(db):
    return baker.make(Category, name='Electronics', slug='electronics', is_active=True)


@pytest.fixture
def seller(db, user):
    return baker.make(Seller, user=user, store_name='Test Store')


@pytest.fixture
def product(db, seller, category):
    return baker.make(
        Product,
        seller=seller,
        category=category,
        name='Laptop',
        slug='laptop',
        description='A powerful laptop',
        brand='Dell',
        is_active=True,
    )


@pytest.fixture
def variant(db, product):
    return baker.make(
        ProductVariant,
        product=product,
        sku='SKU-001',
        price=Decimal('999.99'),
    )


@pytest.fixture
def warehouse(db):
    return baker.make(
        Warehouse,
        name='Main Warehouse',
        address='123 Main St',
        city='Dhaka',
        country='Bangladesh',
    )


@pytest.fixture
def inventory(db, variant, warehouse):
    return baker.make(
        Inventory,
        variant=variant,
        warehouse=warehouse,
        quantity=100,
        reserved=0,
    )


# ── Category Tests ────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCategoryListCreateAPI:
    def test_list_categories(self, api_client, category):
        url = reverse('category-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Electronics'

    def test_list_categories_excludes_inactive(self, api_client):
        baker.make(Category, name='Hidden', slug='hidden', is_active=False)
        url = reverse('category-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_create_category(self, auth_client):
        url = reverse('category-list-create')
        data = {'name': 'Clothing', 'slug': 'clothing'}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Clothing'

    def test_create_category_requires_auth(self, api_client):
        url = reverse('category-list-create')
        data = {'name': 'Clothing', 'slug': 'clothing'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_category_by_slug(self, api_client, category):
        url = reverse('category-detail', kwargs={'slug': 'electronics'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Electronics'

    def test_get_category_by_slug_404(self, api_client):
        url = reverse('category-detail', kwargs={'slug': 'nonexistent'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Seller Tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSellerCreateAPI:
    def test_create_seller(self, auth_client):
        url = reverse('seller-create')
        data = {'store_name': 'My Store'}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['store_name'] == 'My Store'

    def test_create_seller_requires_auth(self, api_client):
        url = reverse('seller-create')
        data = {'store_name': 'My Store'}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_duplicate_seller(self, auth_client, seller):
        url = reverse('seller-create')
        data = {'store_name': 'Another Store'}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_409_CONFLICT


# ── Product Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestProductListCreateAPI:
    def test_list_products(self, api_client, product):
        url = reverse('product-list-create')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_products_filter_by_category(self, api_client, product, category):
        url = reverse('product-list-create')
        response = api_client.get(url, {'category': 'electronics'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_list_products_filter_by_brand(self, api_client, product):
        url = reverse('product-list-create')
        response = api_client.get(url, {'brand': 'Dell'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_product(self, auth_client, seller, category):
        url = reverse('product-list-create')
        data = {
            'name': 'Mouse',
            'description': 'Wireless mouse',
            'category_id': category.id,
            'brand': 'Logitech',
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Mouse'

    def test_create_product_requires_auth(self, api_client, category):
        url = reverse('product-list-create')
        data = {
            'name': 'Mouse',
            'description': 'Wireless mouse',
            'category_id': category.id,
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product_without_seller_profile(self, auth_client, category):
        url = reverse('product-list-create')
        data = {
            'name': 'Mouse',
            'description': 'Wireless mouse',
            'category_id': category.id,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_product_by_slug(self, api_client, product):
        url = reverse('product-detail', kwargs={'slug': 'laptop'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Laptop'
        assert 'variants' in response.data
        assert 'images' in response.data

    def test_get_product_by_slug_404(self, api_client):
        url = reverse('product-detail', kwargs={'slug': 'nonexistent'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_product(self, auth_client, product):
        url = reverse('product-detail', kwargs={'slug': 'laptop'})
        data = {'name': 'Updated Laptop'}
        response = auth_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Laptop'

    def test_deactivate_product(self, auth_client, product):
        url = reverse('product-deactivate', kwargs={'slug': 'laptop'})
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        product.refresh_from_db()
        assert product.is_active is False


# ── Variant Tests ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestProductVariantCreateAPI:
    def test_create_variant(self, auth_client, product):
        url = reverse('product-variant-create', kwargs={'slug': 'laptop'})
        data = {
            'sku': 'SKU-002',
            'price': '499.99',
            'attributes': {'color': 'silver', 'size': '15inch'},
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['sku'] == 'SKU-002'

    def test_create_variant_duplicate_sku(self, auth_client, product, variant):
        url = reverse('product-variant-create', kwargs={'slug': 'laptop'})
        data = {'sku': 'SKU-001', 'price': '299.99'}
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_create_variant_duplicate_attributes(self, auth_client, product, variant):
        baker.make(VariantAttribute, variant=variant, key=baker.make(AttributeKey, name='color'), value='red')
        url = reverse('product-variant-create', kwargs={'slug': 'laptop'})
        data = {
            'sku': 'SKU-003',
            'price': '599.99',
            'attributes': {'color': 'red'},
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_409_CONFLICT


# ── Warehouse Tests ───────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestWarehouseCreateAPI:
    def test_create_warehouse(self, auth_client):
        url = reverse('warehouse-create')
        data = {
            'name': 'Warehouse 2',
            'address': '456 Side St',
            'city': 'Chittagong',
            'country': 'Bangladesh',
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Warehouse 2'


# ── Inventory Tests ───────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestInventoryAPI:
    def test_get_inventory_for_variant(self, api_client, inventory):
        url = reverse('inventory-by-variant', kwargs={'variant_id': inventory.variant.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_initialize_inventory(self, auth_client, variant, warehouse):
        url = reverse('inventory-initialize')
        data = {
            'variant_id': variant.id,
            'warehouse_id': warehouse.id,
            'quantity': 50,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == 50

    def test_initialize_inventory_duplicate(self, auth_client, inventory):
        url = reverse('inventory-initialize')
        data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 50,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_reconcile_inventory(self, auth_client, inventory):
        url = reverse('inventory-reconcile')
        data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 200,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['quantity'] == 200

    def test_reserve_inventory(self, auth_client, inventory):
        url = reverse('inventory-reserve')
        data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 10,
            'idempotency_key': 'order-1',
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['quantity'] == 10
        assert response.data['status'] == 'active'

    def test_reserve_inventory_insufficient_stock(self, auth_client, inventory):
        url = reverse('inventory-reserve')
        data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 999,
            'idempotency_key': 'order-2',
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_release_reservation(self, auth_client, inventory):
        reserve_url = reverse('inventory-reserve')
        reserve_data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 10,
            'idempotency_key': 'order-3',
        }
        reserve_response = auth_client.post(reserve_url, reserve_data)
        reservation_id = reserve_response.data['id']

        release_url = reverse('reservation-release', kwargs={'reservation_id': reservation_id})
        response = auth_client.post(release_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'released'

    def test_confirm_reservation(self, auth_client, inventory):
        reserve_url = reverse('inventory-reserve')
        reserve_data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 10,
            'idempotency_key': 'order-4',
        }
        reserve_response = auth_client.post(reserve_url, reserve_data)
        reservation_id = reserve_response.data['id']

        confirm_url = reverse('reservation-confirm', kwargs={'reservation_id': reservation_id})
        response = auth_client.post(confirm_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'

        inventory.refresh_from_db()
        assert inventory.quantity == 90
        assert inventory.reserved == 0

    def test_release_confirmed_reservation_fails(self, auth_client, inventory):
        reserve_url = reverse('inventory-reserve')
        reserve_data = {
            'variant_id': inventory.variant.id,
            'warehouse_id': inventory.warehouse.id,
            'quantity': 10,
            'idempotency_key': 'order-5',
        }
        reserve_response = auth_client.post(reserve_url, reserve_data)
        reservation_id = reserve_response.data['id']

        confirm_url = reverse('reservation-confirm', kwargs={'reservation_id': reservation_id})
        auth_client.post(confirm_url)

        release_url = reverse('reservation-release', kwargs={'reservation_id': reservation_id})
        response = auth_client.post(release_url)
        assert response.status_code == status.HTTP_409_CONFLICT
