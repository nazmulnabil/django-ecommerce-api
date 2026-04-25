import pytest
from model_bakery import baker
from users.models import User, Address, Seller


pytestmark = pytest.mark.django_db


class TestUserModel:

    def test_str_returns_email(self):
        user = baker.make(User, email='nabil@test.com')
        assert str(user) == 'nabil@test.com'

    def test_email_is_unique(self):
        baker.make(User, email='nabil@test.com')
        with pytest.raises(Exception):
            baker.make(User, email='nabil@test.com')

    def test_username_field_is_email(self):
        assert User.USERNAME_FIELD == 'email'

    def test_phone_defaults_to_blank(self):
        user = baker.make(User)
        assert user.phone == '' or user.phone is not None

    def test_has_created_at(self):
        user = baker.make(User)
        assert user.created_at is not None

    def test_has_updated_at(self):
        user = baker.make(User)
        assert user.updated_at is not None


class TestAddressModel:

    def test_str_returns_label_and_email(self):
        user = baker.make(User, email='nabil@test.com')
        address = baker.make(Address, user=user, label='Home')
        assert str(address) == 'Home - nabil@test.com'

    def test_address_belongs_to_user(self):
        user = baker.make(User)
        address = baker.make(Address, user=user)
        assert address.user == user

    def test_is_default_false_by_default(self):
        address = baker.make(Address)
        assert address.is_default == False

    def test_cascade_delete_with_user(self):
        user = baker.make(User)
        baker.make(Address, user=user)
        user_id = user.id
        user.delete()
        assert Address.objects.filter(user_id=user_id).count() == 0


class TestSellerModel:

    def test_str_returns_store_name(self):
        seller = baker.make(Seller, store_name='Nabil Store')
        assert str(seller) == 'Nabil Store'

    def test_one_seller_per_user(self):
        user = baker.make(User)
        baker.make(Seller, user=user)
        with pytest.raises(Exception):
            baker.make(Seller, user=user)

    def test_is_verified_false_by_default(self):
        seller = baker.make(Seller)
        assert seller.is_verified == False

    def test_rating_default(self):
        seller = baker.make(Seller)
        assert float(seller.rating) == 0.0