from core.exceptions import DomainException


class CategoryNotFoundError(DomainException):
    pass

class ProductNotFoundError(DomainException):
    pass

class SellerNotFoundError(DomainException):
    pass

class SellerAlreadyExistsError(DomainException):
    pass

class WarehouseNotFoundError(DomainException):
    pass

class InventoryNotFoundError(DomainException):
    pass

class DuplicateSkuError(DomainException):
    pass

class DuplicateVariantError(DomainException):
    pass

class InsufficientStockError(DomainException):
    pass

class NegativeInventoryError(DomainException):
    pass

class InvalidInventoryOperationError(DomainException):
    pass