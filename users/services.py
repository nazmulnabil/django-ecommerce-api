# users/services.py

from django.db import transaction, IntegrityError
from django.contrib.auth import authenticate

from .models import User, Address, Seller
from .exceptions import (
    EmailAlreadyExistsError,
    AddressNotFoundError,
    SellerAlreadyExistsError,
    InvalidCredentialsError,
)


def register_user(
    *,
    email: str,
    username: str,
    password: str,
    phone: str = '',
) -> User:
    try:
        return User.objects.create_user(
            email=email,
            username=username,
            password=password,
            phone=phone,
        )
    except IntegrityError:
        raise EmailAlreadyExistsError(f"Email {email} is already registered.")


def authenticate_user(*, email: str, password: str) -> User:
    user = authenticate(username=email, password=password)
    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")
    return user


def update_user_profile(
    *,
    user: User,
    phone: str | None = None,
    username: str | None = None,
) -> User:
    update_fields = []
    if phone is not None:
        user.phone = phone
        update_fields.append('phone')
    if username is not None:
        user.username = username
        update_fields.append('username')
    if update_fields:
        user.save(update_fields=update_fields)
    return user


def create_address(
    *,
    user: User,
    label: str,
    street: str,
    city: str,
    country: str,
    postal_code: str,
    is_default: bool = False,
) -> Address:
    with transaction.atomic():
        if is_default:
            Address.objects.filter(user=user).update(is_default=False)
        return Address.objects.create(
            user=user,
            label=label,
            street=street,
            city=city,
            country=country,
            postal_code=postal_code,
            is_default=is_default,
        )


def set_default_address(*, user: User, address_id: int) -> Address:
    with transaction.atomic():
        try:
            address = (
                Address.objects
                .select_for_update()
                .get(id=address_id, user=user)
            )
        except Address.DoesNotExist:
            raise AddressNotFoundError(f"Address {address_id} not found.")

        Address.objects.filter(user=user).update(is_default=False)
        address.is_default = True
        address.save(update_fields=['is_default'])
        return address


def delete_address(*, user: User, address_id: int) -> None:
    try:
        address = Address.objects.get(id=address_id, user=user)
    except Address.DoesNotExist:
        raise AddressNotFoundError(f"Address {address_id} not found.")
    address.delete()


def register_seller(*, user: User, store_name: str) -> Seller:
    if Seller.objects.filter(user=user).exists():
        raise SellerAlreadyExistsError("User is already a registered seller.")
    return Seller.objects.create(user=user, store_name=store_name)