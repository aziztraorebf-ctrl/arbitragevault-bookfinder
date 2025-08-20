"""Custom application exceptions."""


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DuplicateEmailError(AppException):
    """Raised when trying to create user with existing email."""
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email '{email}' already exists",
            details={"email": email}
        )


class InvalidStatusTransitionError(AppException):
    """Raised when trying to perform invalid batch status transition."""
    def __init__(self, from_status: str, to_status: str, batch_id: str = None):
        super().__init__(
            message=f"Invalid status transition from '{from_status}' to '{to_status}'",
            details={"from_status": from_status, "to_status": to_status, "batch_id": batch_id}
        )


class InvalidFilterFieldError(AppException):
    """Raised when trying to filter/sort by non-whitelisted field."""
    def __init__(self, field: str, allowed_fields: list):
        super().__init__(
            message=f"Field '{field}' not allowed for filtering/sorting. Allowed: {allowed_fields}",
            details={"field": field, "allowed_fields": allowed_fields}
        )


class InvalidTransitionError(AppException):
    """Raised when trying to perform invalid state transition."""
    def __init__(self, message: str, from_state: str = None, to_state: str = None):
        super().__init__(
            message=message,
            details={"from_state": from_state, "to_state": to_state}
        )