from functools import wraps

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


class ConditionalLimiter(Limiter):
    """Limiter that can be disabled via settings."""
    
    def limit(self, limit_value):
        """Return decorator that only applies limit if enabled."""
        def decorator(func):
            if settings.rate_limit_enabled:
                return super(ConditionalLimiter, self).limit(limit_value)(func)
            return func
        return decorator


limiter = ConditionalLimiter(key_func=get_remote_address)


def conditional_limit(limit_string: str):
    """Apply rate limit only if RATE_LIMIT_ENABLED is True."""
    def decorator(func):
        if settings.rate_limit_enabled:
            return limiter.limit(limit_string)(func)
        return func
    return decorator
