import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from model_bakery import baker
from users.models import User, Address, Seller
from users.services import register_user


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user():
    return register_user(
        email='nabil@test.com',
        username='nabil',
        password='securepass123',
    )


@pytest.fixture
def auth_client(registered_user):
    client = APIClient()
    response = client.post('/api/v1/auth/login/', {
        'email': 'nabil@test.com',
        'password': 'securepass123',
    })
    token = response.data['tokens']['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ─────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────

class TestRegisterView:

    def test_register_success(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'nabil@test.com',
            'username': 'nabil',
            'password': 'securepass123',
        })
        assert response.status_code == 201
        assert response.data['user']['email'] == 'nabil@test.com'
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_register_returns_hashed_password_never_in_response(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'nabil@test.com',
            'username': 'nabil',
            'password': 'securepass123',
        })
        assert 'password' not in response.data['user']

    def test_register_duplicate_email_returns_409(self, client, registered_user):
        response = client.post('/api/v1/auth/register/', {
            'email': 'nabil@test.com',
            'username': 'nabil2',
            'password': 'securepass123',
        })
        assert response.status_code == 409

    def test_register_invalid_email_returns_400(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'not-an-email',
            'username': 'nabil',
            'password': 'securepass123',
        })
        assert response.status_code == 400

    def test_register_short_password_returns_400(self, client):
        response = client.post('/api/v1/auth/register/', {
            'email': 'nabil@test.com',
            'username': 'nabil',
            'password': '123',
        })
        assert response.status_code == 400


# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────

class TestLoginView:

    def test_login_success(self, client, registered_user):
        response = client.post('/api/v1/auth/login/', {
            'email': 'nabil@test.com',
            'password': 'securepass123',
        })
        assert response.status_code == 200
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']

    def test_login_wrong_password_returns_401(self, client, registered_user):
        response = client.post('/api/v1/auth/login/', {
            'email': 'nabil@test.com',
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        response = client.post('/api/v1/auth/login/', {
            'email': 'ghost@test.com',
            'password': 'securepass123',
        })
        assert response.status_code == 401


# ─────────────────────────────────────────
# ME
# ─────────────────────────────────────────

class TestMeView:

    def test_get_profile_authenticated(self, auth_client, registered_user):
        response = auth_client.get('/api/v1/auth/users/me/')
        assert response.status_code == 200
        assert response.data['email'] == 'nabil@test.com'

    def test_get_profile_unauthenticated_returns_401(self, client):
        response = client.get('/api/v1/auth/users/me/')
        assert response.status_code == 401

    def test_update_profile(self, auth_client):
        response = auth_client.patch('/api/v1/auth/users/me/', {
            'phone': '01712345678',
        })
        assert response.status_code == 200
        assert response.data['phone'] == '01712345678'

    def test_update_profile_unauthenticated_returns_401(self, client):
        response = client.patch('/api/v1/auth/users/me/', {
            'phone': '01712345678',
        })
        assert response.status_code == 401


# ─────────────────────────────────────────
# ADDRESSES
# ─────────────────────────────────────────

class TestAddressListCreateView:

    def test_create_address(self, auth_client):
        response = auth_client.post('/api/v1/auth/users/me/addresses/', {
            'label': 'Home',
            'street': '123 Main St',
            'city': 'Dhaka',
            'country': 'Bangladesh',
            'postal_code': '1207',
        })
        assert response.status_code == 201
        assert response.data['label'] == 'Home'

    def test_list_addresses(self, auth_client, registered_user):
        baker.make(Address, user=registered_user, _quantity=3)
        response = auth_client.get('/api/v1/auth/users/me/addresses/')
        assert response.status_code == 200
        assert len(response.data) == 3

    def test_list_addresses_unauthenticated_returns_401(self, client):
        response = client.get('/api/v1/auth/users/me/addresses/')
        assert response.status_code == 401

    def test_create_address_missing_field_returns_400(self, auth_client):
        response = auth_client.post('/api/v1/auth/users/me/addresses/', {
            'label': 'Home',
            # missing street, city, country, postal_code
        })
        assert response.status_code == 400


class TestAddressDetailView:

    def test_set_default_address(self, auth_client, registered_user):
        address = baker.make(Address, user=registered_user, is_default=False)
        response = auth_client.patch(
            f'/api/v1/auth/users/me/addresses/{address.id}/'
        )
        assert response.status_code == 200
        assert response.data['is_default'] == True

    def test_delete_address(self, auth_client, registered_user):
        address = baker.make(Address, user=registered_user)
        response = auth_client.delete(
            f'/api/v1/auth/users/me/addresses/{address.id}/'
        )
        assert response.status_code == 204
        assert Address.objects.filter(id=address.id).count() == 0

    def test_delete_address_not_found_returns_404(self, auth_client):
        response = auth_client.delete('/api/v1/auth/users/me/addresses/99999/')
        assert response.status_code == 404

    def test_cannot_delete_another_users_address(self, auth_client):
        other_user = baker.make(User)
        address = baker.make(Address, user=other_user)
        response = auth_client.delete(
            f'/api/v1/auth/users/me/addresses/{address.id}/'
        )
        assert response.status_code == 404


# ─────────────────────────────────────────
# SELLER
# ─────────────────────────────────────────

class TestSellerRegisterView:

    def test_register_seller(self, auth_client):
        response = auth_client.post('/api/v1/auth/seller/register/', {
            'store_name': 'Nabil Store',
        })
        assert response.status_code == 201
        assert response.data['store_name'] == 'Nabil Store'

    def test_register_seller_twice_returns_409(self, auth_client):
        auth_client.post('/api/v1/auth/seller/register/', {
            'store_name': 'Nabil Store',
        })
        response = auth_client.post('/api/v1/auth/seller/register/', {
            'store_name': 'Another Store',
        })
        assert response.status_code == 409

    def test_register_seller_unauthenticated_returns_401(self, client):
        response = client.post('/api/v1/auth/seller/register/', {
            'store_name': 'Nabil Store',
        })
        assert response.status_code == 401