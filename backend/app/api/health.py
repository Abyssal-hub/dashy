from fastapi import APIRouter
from pydantic import BaseModel

from app.db.database import check_db_health
from app.services.redis_client import check_redis_health

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_healthy = await check_db_health()
    redis_healthy = await check_redis_health()

    db_status = "healthy" if db_healthy else "unhealthy"
    redis_status = "healthy" if redis_healthy else "unhealthy"
    overall_status = "healthy" if (db_healthy and redis_healthy) else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
    )
