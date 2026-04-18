from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from app.api import portfolio as portfolio_router
from app.api import calendar as calendar_router
from app.api import ingest as ingest_router


# Path to frontend static files
# In Docker: mounted at /frontend
# Local dev: relative to backend/app/main.py
FRONTEND_DIR = Path("/frontend") if Path("/frontend").exists() else Path(__file__).parent.parent.parent / "frontend"


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

    # Register API routers
    app.include_router(health.router)
    app.include_router(auth_router.router)
    app.include_router(protected.router)
    app.include_router(modules_router, prefix="/api")
    app.include_router(dashboard_router.router, prefix="/api")
    app.include_router(portfolio_router.router, prefix="/api")
    app.include_router(calendar_router.router, prefix="/api")
    app.include_router(ingest_router.router, prefix="/api")

    # Serve static files from frontend directory
    if FRONTEND_DIR.exists():
        app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
        
        # Serve index.html at root and /index.html
        @app.get("/")
        async def serve_index():
            from fastapi.responses import FileResponse
            return FileResponse(FRONTEND_DIR / "index.html")

        @app.get("/index.html")
        async def serve_index_html():
            from fastapi.responses import FileResponse
            return FileResponse(FRONTEND_DIR / "index.html")

        # Serve dashboard.html at /dashboard and /dashboard.html
        @app.get("/dashboard")
        async def serve_dashboard():
            from fastapi.responses import FileResponse
            return FileResponse(FRONTEND_DIR / "dashboard.html")

        @app.get("/dashboard.html")
        async def serve_dashboard_html():
            from fastapi.responses import FileResponse
            return FileResponse(FRONTEND_DIR / "dashboard.html")

    return app


# Factory function for uvicorn --factory flag
def app_factory() -> FastAPI:
    """Factory function for creating the FastAPI app."""
    return create_app()


# For backwards compatibility and non-factory usage
app = create_app()
