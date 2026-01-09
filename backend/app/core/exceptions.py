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


class NotFoundError(AppException):
    """Raised when resource not found."""
    def __init__(self, resource_type: str, resource_id: str = None):
        super().__init__(
            message=f"{resource_type} not found",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ConflictError(AppException):
    """Raised when resource conflict occurs."""
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(
            message=message,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class InsufficientTokensError(AppException):
    """Raised when Keepa API token balance is too low to proceed with request."""
    def __init__(self, current_balance: int, required_tokens: int, endpoint: str = None):
        super().__init__(
            message=f"Insufficient Keepa tokens: {current_balance} available, {required_tokens} required",
            details={
                "current_balance": current_balance,
                "required_tokens": required_tokens,
                "endpoint": endpoint,
                "deficit": required_tokens - current_balance
            }
        )


class KeepaRateLimitError(AppException):
    """
    Raised when Keepa API returns HTTP 429 (rate limit exceeded).

    This exception is designed to be caught by tenacity @retry decorator
    for automatic exponential backoff retry.
    """
    def __init__(self, tokens_left: str = "unknown", endpoint: str = None, retry_after: int = None):
        super().__init__(
            message=f"Keepa API rate limit exceeded (HTTP 429). Tokens left: {tokens_left}",
            details={
                "tokens_left": tokens_left,
                "endpoint": endpoint,
                "retry_after": retry_after,
                "error_type": "rate_limit"
            }
        )
        self.tokens_left = tokens_left
        self.retry_after = retry_after


class InvalidCredentialsError(AppException):
    """Raised when login credentials are invalid."""
    def __init__(self):
        super().__init__(
            message="Invalid email or password",
            details={"error_code": "INVALID_CREDENTIALS"}
        )


class AccountLockedError(AppException):
    """Raised when account is temporarily locked."""
    def __init__(self, locked_until: str = None):
        super().__init__(
            message="Account temporarily locked due to too many failed attempts",
            details={"error_code": "ACCOUNT_LOCKED", "locked_until": locked_until}
        )


class AccountInactiveError(AppException):
    """Raised when account is deactivated."""
    def __init__(self):
        super().__init__(
            message="Account is deactivated",
            details={"error_code": "ACCOUNT_INACTIVE"}
        )


class InvalidTokenError(AppException):
    """Raised when JWT token is invalid or expired."""
    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(
            message=reason,
            details={"error_code": "INVALID_TOKEN"}
        )


class WeakPasswordError(AppException):
    """Raised when password doesn't meet strength requirements."""
    def __init__(self, errors: list):
        super().__init__(
            message="Password does not meet security requirements",
            details={"error_code": "WEAK_PASSWORD", "validation_errors": errors}
        )