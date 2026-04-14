from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.db.database import init_db, close_db
from app.services.redis_client import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_db()
    await init_redis()
    yield
    # Shutdown
    await close_redis()
    await close_db()
