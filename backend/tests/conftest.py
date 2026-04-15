import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Disable rate limiting BEFORE importing app
from app.core.config import settings
settings.rate_limit_enabled = False

from app.main import create_app
from app.db.database import Base, get_db_session
from app.services.redis_client import get_redis_client


@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    """Spin up PostgreSQL container for test session."""
    with PostgresContainer("postgres:15", driver="asyncpg") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def redis_container():
    """Spin up Redis container for test session."""
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest_asyncio.fixture
async def db_engine(postgres_container):
    """Create SQLAlchemy engine connected to test PostgreSQL."""
    database_url = postgres_container.get_connection_url()
    engine = create_async_engine(database_url, future=True, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    """Provide a database session for tests."""
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine, redis_container):
    """Create test client with real DB and Redis."""
    app = create_app()
    
    # Override database dependency
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    # Override Redis dependency
    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{redis_host}:{redis_port}/0"
    import redis.asyncio as redis
    test_redis = redis.from_url(redis_url, decode_responses=True)
    
    def override_get_redis():
        return test_redis
    
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.test_redis = test_redis
        yield ac
    
    await test_redis.aclose()
    app.dependency_overrides.clear()
