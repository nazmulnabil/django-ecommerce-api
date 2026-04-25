# core/exceptions.py

class DomainException(Exception):
    """
    Base class for all domain-level exceptions.
    Never use HTTP status codes here.
    Services raise these. Views catch and map to HTTP.
    """
    pass