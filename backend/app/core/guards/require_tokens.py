"""
Guard decorator for Keepa token control.
Blocks endpoint execution if insufficient tokens available.
"""
from functools import wraps
from fastapi import HTTPException, Depends
from app.services.keepa_service import get_keepa_service, KeepaService


def require_tokens(action: str):
    """
    Decorator to guard endpoints with token availability check.

    Usage:
        @router.post("/discover")
        @require_tokens("surprise_me")
        async def discover_niche(keepa: KeepaService = Depends(get_keepa_service)):
            # This only executes if sufficient tokens available
            ...

    Args:
        action: Business action name from TOKEN_COSTS registry

    Raises:
        HTTPException 429: If insufficient tokens for action
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract KeepaService from kwargs (injected by FastAPI)
            keepa_service = kwargs.get('keepa')

            if keepa_service is None:
                raise ValueError(
                    "require_tokens decorator requires KeepaService "
                    "dependency: keepa: KeepaService = Depends(get_keepa_service)"
                )

            # Check token availability
            check = await keepa_service.can_perform_action(action)

            if not check["can_proceed"]:
                deficit = check['required_tokens'] - check['current_balance']

                # Create custom response body with all token info
                error_response = {
                    "detail": f"Insufficient Keepa tokens for action '{action}'. "
                              f"Required: {check['required_tokens']}, "
                              f"Available: {check['current_balance']}, "
                              f"Deficit: {deficit}",
                    "current_balance": check["current_balance"],
                    "required_tokens": check["required_tokens"],
                    "deficit": deficit
                }

                raise HTTPException(
                    status_code=429,
                    detail=error_response,
                    headers={
                        "X-Token-Balance": str(check["current_balance"]),
                        "X-Token-Required": str(check["required_tokens"]),
                        "Retry-After": "3600"  # Suggest retry in 1 hour
                    }
                )

            # Tokens sufficient - proceed with execution
            return await func(*args, **kwargs)

        return wrapper
    return decorator
