import redis.asyncio as redis
from app.core.config import settings

_redis_client: redis.Redis | None = None


async def init_redis() -> None:
    global _redis_client
    _redis_client = redis.from_url(
        settings.redis_url,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        decode_responses=True,
    )


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_redis_client() -> redis.Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def check_redis_health() -> bool:
    if _redis_client is None:
        return False
    try:
        await _redis_client.ping()
        return True
    except Exception:
        return False
