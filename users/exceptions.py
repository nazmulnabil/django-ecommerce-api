
from core.exceptions import DomainException


class EmailAlreadyExistsError(DomainException):
    pass


class AddressNotFoundError(DomainException):
    pass


class SellerAlreadyExistsError(DomainException):
    pass


class InvalidCredentialsError(DomainException):
    pass

class UserNotFoundError(DomainException):     
    pass