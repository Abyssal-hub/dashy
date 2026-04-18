from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.db.database import init_db, close_db
from app.services.redis_client import init_redis, close_redis
from app.services.consumer import start_consumer, stop_consumer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    await init_db()
    await init_redis()
    # Start Redis consumer background task per DEV-009
    await start_consumer()
    yield
    # Shutdown - graceful stop of consumer before closing connections
    await stop_consumer()
    await close_redis()
    await close_db()
