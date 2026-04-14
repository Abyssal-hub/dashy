from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.lifespan import lifespan
from app.core.limiter import limiter
from app.api import health
from app.api.auth import router as auth_router
from app.api import protected
from app.api.modules import router as modules_router
from app.api import dashboard as dashboard_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Personal Monitoring Dashboard API",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health.router)
    app.include_router(auth_router.router)
    app.include_router(protected.router)
    app.include_router(modules_router, prefix="/api")
    app.include_router(dashboard_router.router, prefix="/api")

    return app


app_factory = create_app()
