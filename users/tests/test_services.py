import pytest
from model_bakery import baker
from users.models import User, Address, Seller
from users.services import (
    register_user,
    authenticate_user,
    update_user_profile,
    create_address,
    set_default_address,
    delete_address,
    register_seller,
)
from users.exceptions import (
    EmailAlreadyExistsError,
    AddressNotFoundError,
    SellerAlreadyExistsError,
    InvalidCredentialsError,
)


pytestmark = pytest.mark.django_db


class TestRegisterUser:

    def test_creates_user_successfully(self):
        user = register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
        )
        assert user.id is not None
        assert user.email == 'nabil@test.com'
        assert user.username == 'nabil'

    def test_password_is_hashed(self):
        user = register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
        )
        assert user.password != 'securepass123'
        assert user.check_password('securepass123')

    def test_phone_defaults_to_empty(self):
        user = register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
        )
        assert user.phone == ''

    def test_phone_saved_when_provided(self):
        user = register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
            phone='01712345678',
        )
        assert user.phone == '01712345678'

    def test_raises_if_email_already_exists(self):
        baker.make(User, email='nabil@test.com')
        with pytest.raises(EmailAlreadyExistsError):
            register_user(
                email='nabil@test.com',
                username='nabil2',
                password='securepass123',
            )


class TestAuthenticateUser:

    def test_returns_user_with_valid_credentials(self):
        register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
        )
        user = authenticate_user(email='nabil@test.com', password='securepass123')
        assert user.email == 'nabil@test.com'

    def test_raises_with_wrong_password(self):
        register_user(
            email='nabil@test.com',
            username='nabil',
            password='securepass123',
        )
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email='nabil@test.com', password='wrongpassword')

    def test_raises_with_nonexistent_email(self):
        with pytest.raises(InvalidCredentialsError):
            authenticate_user(email='ghost@test.com', password='securepass123')


class TestUpdateUserProfile:

    def test_updates_phone(self):
        user = baker.make(User)
        updated = update_user_profile(user=user, phone='01712345678')
        assert updated.phone == '01712345678'

    def test_updates_username(self):
        user = baker.make(User)
        updated = update_user_profile(user=user, username='newname')
        assert updated.username == 'newname'

    def test_updates_only_provided_fields(self):
        user = baker.make(User, username='original')
        updated = update_user_profile(user=user, phone='01712345678')
        assert updated.username == 'original'
        assert updated.phone == '01712345678'

    def test_no_update_when_nothing_provided(self):
        user = baker.make(User, username='original', phone='0171')
        updated = update_user_profile(user=user)
        assert updated.username == 'original'
        assert updated.phone == '0171'


class TestCreateAddress:

    def test_creates_address_for_user(self):
        user = baker.make(User)
        address = create_address(
            user=user,
            label='Home',
            street='123 Main St',
            city='Dhaka',
            country='Bangladesh',
            postal_code='1207',
        )
        assert address.id is not None
        assert address.user == user
        assert address.label == 'Home'

    def test_is_default_false_by_default(self):
        user = baker.make(User)
        address = create_address(
            user=user,
            label='Home',
            street='123 Main St',
            city='Dhaka',
            country='Bangladesh',
            postal_code='1207',
        )
        assert address.is_default == False

    def test_setting_default_resets_others(self):
        user = baker.make(User)
        first = create_address(
            user=user,
            label='Home',
            street='123 Main St',
            city='Dhaka',
            country='Bangladesh',
            postal_code='1207',
            is_default=True,
        )
        second = create_address(
            user=user,
            label='Work',
            street='456 Office Rd',
            city='Dhaka',
            country='Bangladesh',
            postal_code='1208',
            is_default=True,
        )
        first.refresh_from_db()
        assert first.is_default == False
        assert second.is_default == True


class TestSetDefaultAddress:

    def test_sets_address_as_default(self):
        user = baker.make(User)
        address = baker.make(Address, user=user, is_default=False)
        result = set_default_address(user=user, address_id=address.id)
        assert result.is_default == True

    def test_resets_previous_default(self):
        user = baker.make(User)
        old_default = baker.make(Address, user=user, is_default=True)
        new_address = baker.make(Address, user=user, is_default=False)
        set_default_address(user=user, address_id=new_address.id)
        old_default.refresh_from_db()
        assert old_default.is_default == False

    def test_raises_if_address_not_found(self):
        user = baker.make(User)
        with pytest.raises(AddressNotFoundError):
            set_default_address(user=user, address_id=99999)

    def test_cannot_set_another_users_address_as_default(self):
        user1 = baker.make(User)
        user2 = baker.make(User)
        address = baker.make(Address, user=user2)
        with pytest.raises(AddressNotFoundError):
            set_default_address(user=user1, address_id=address.id)


class TestDeleteAddress:

    def test_deletes_address(self):
        user = baker.make(User)
        address = baker.make(Address, user=user)
        delete_address(user=user, address_id=address.id)
        assert Address.objects.filter(id=address.id).count() == 0

    def test_raises_if_address_not_found(self):
        user = baker.make(User)
        with pytest.raises(AddressNotFoundError):
            delete_address(user=user, address_id=99999)

    def test_cannot_delete_another_users_address(self):
        user1 = baker.make(User)
        user2 = baker.make(User)
        address = baker.make(Address, user=user2)
        with pytest.raises(AddressNotFoundError):
            delete_address(user=user1, address_id=address.id)


class TestRegisterSeller:

    def test_creates_seller(self):
        user = baker.make(User)
        seller = register_seller(user=user, store_name='Nabil Store')
        assert seller.id is not None
        assert seller.store_name == 'Nabil Store'
        assert seller.user == user

    def test_raises_if_already_a_seller(self):
        user = baker.make(User)
        register_seller(user=user, store_name='Nabil Store')
        with pytest.raises(SellerAlreadyExistsError):
            register_seller(user=user, store_name='Another Store')

    def test_is_verified_false_by_default(self):
        user = baker.make(User)
        seller = register_seller(user=user, store_name='Nabil Store')
        assert seller.is_verified == False