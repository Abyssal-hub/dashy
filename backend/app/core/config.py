from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "Personal Monitoring Dashboard"
    environment: str = "local"
    frontend_url: str = "http://localhost:3000"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/dbname"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    # Auth
    jwt_secret: str = "change-me-in-production"
    argon2_secret: Optional[str] = None
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Email
    resend_api_key: Optional[str] = None
    alert_from_email: Optional[str] = None


settings = Settings()
