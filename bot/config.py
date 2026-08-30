"""Application configuration management."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Convert PostgreSQL URLs to the asyncpg async driver.

    Hosts such as Render provide ``postgresql://`` or ``postgres://`` URLs, which
    SQLAlchemy would resolve to psycopg2. This project uses create_async_engine
    with asyncpg instead.

    Args:
        url: Raw database URL from the environment.

    Returns:
        URL suitable for create_async_engine (SQLite URLs are unchanged).
    """
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str

    # Environment
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    # Admins
    bot_admin_ids: list[int] = []

    # Logging
    log_level: str = "INFO"

    # Listing configuration
    max_listings_per_user: int = 50
    listing_expiry_days: int = 180

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"


def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()  # type: ignore[call-arg]
