# users/selectors.py

from users.exceptions import UserNotFoundError

from .models import User, Address


def get_user_by_id(*, user_id: int) -> User:
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise UserNotFoundError(f"User {user_id} not found.")


def get_addresses_for_user(*, user: User):
    return Address.objects.filter(user=user).order_by('-is_default', '-created_at')