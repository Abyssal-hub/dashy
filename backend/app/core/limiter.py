from functools import wraps

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


class ConditionalLimiter(Limiter):
    """Limiter that can be disabled via settings."""
    
    def _check_request(self, request, func, limit_arg):
        """Override to skip rate limiting when disabled."""
        if not settings.rate_limit_enabled:
            return
        return super()._check_request(request, func, limit_arg)


limiter = ConditionalLimiter(key_func=get_remote_address)


def conditional_limit(limit_string: str):
    """Apply rate limit only if RATE_LIMIT_ENABLED is True."""
    def decorator(func):
        # Always apply the limiter, but it will check settings at runtime
        return limiter.limit(limit_string)(func)
    return decorator
