import pytest
from model_bakery import baker
from users.models import User, Address
from users.selectors import get_user_by_id, get_addresses_for_user
from users.exceptions import UserNotFoundError


pytestmark = pytest.mark.django_db


class TestGetUserById:

    def test_returns_user_when_exists(self):
        user = baker.make(User)
        result = get_user_by_id(user_id=user.id)
        assert result.id == user.id

    def test_raises_when_user_not_found(self):
        with pytest.raises(UserNotFoundError):
            get_user_by_id(user_id=99999)


class TestGetAddressesForUser:

    def test_returns_only_users_addresses(self):
        user1 = baker.make(User)
        user2 = baker.make(User)
        baker.make(Address, user=user1, _quantity=3)
        baker.make(Address, user=user2, _quantity=2)
        result = get_addresses_for_user(user=user1)
        assert result.count() == 3

    def test_default_address_comes_first(self):
        user = baker.make(User)
        non_default = baker.make(Address, user=user, is_default=False)
        default = baker.make(Address, user=user, is_default=True)
        result = list(get_addresses_for_user(user=user))
        assert result[0].id == default.id
        assert result[1].id == non_default.id

    def test_returns_empty_when_no_addresses(self):
        user = baker.make(User)
        result = get_addresses_for_user(user=user)
        assert result.count() == 0