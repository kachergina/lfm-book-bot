"""Application configuration management."""

import ssl
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.constants import WEBHOOK_PATH

# libpq query params passed through by SQLAlchemy but not supported by asyncpg
_LIBPQ_QUERY_PARAMS = frozenset(
    {
        "sslcert",
        "sslkey",
        "sslrootcert",
        "sslcrl",
        "sslcompression",
        "channel_binding",
        "gssencmode",
    }
)


def _asyncpg_ssl_from_sslmode(sslmode: str) -> bool | ssl.SSLContext:
    """Map libpq sslmode to asyncpg's ssl connect argument."""
    mode = sslmode.lower()
    if mode == "disable":
        return False
    if mode in ("verify-ca", "verify-full"):
        return ssl.create_default_context()
    return True


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


def prepare_asyncpg_url(url: str) -> tuple[str, dict[str, Any]]:
    """Prepare a database URL and connect_args for create_async_engine.

    Neon and similar hosts append libpq ``sslmode`` to ``DATABASE_URL``. SQLAlchemy
    forwards query parameters to asyncpg.connect(), which does not accept
    ``sslmode``. This function strips unsupported params and maps ``sslmode`` to
    asyncpg's ``ssl`` argument.

    Args:
        url: Database URL (raw or already normalized).

    Returns:
        Tuple of (engine URL, connect_args). SQLite URLs return empty connect_args.
    """
    url = normalize_database_url(url)
    if url.startswith("sqlite"):
        return url, {}

    parsed = urlparse(url)
    if "+asyncpg" not in parsed.scheme:
        return url, {}

    connect_args: dict[str, Any] = {}
    kept_params: list[tuple[str, str]] = []

    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "sslmode":
            connect_args["ssl"] = _asyncpg_ssl_from_sslmode(value)
        elif key in _LIBPQ_QUERY_PARAMS:
            continue
        else:
            kept_params.append((key, value))

    cleaned = urlunparse(parsed._replace(query=urlencode(kept_params)))
    return cleaned, connect_args


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    telegram_bot_token: str
    telegram_mode: str = "polling"
    telegram_webhook_secret: str | None = None

    # Render / webhook
    port: int = 8000
    render_external_url: str | None = None

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

    @field_validator("telegram_mode", mode="before")
    @classmethod
    def _normalize_telegram_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.lower()
        return value

    @field_validator("telegram_mode")
    @classmethod
    def _validate_telegram_mode(cls, value: str) -> str:
        if value not in {"polling", "webhook"}:
            msg = "TELEGRAM_MODE must be 'polling' or 'webhook'"
            raise ValueError(msg)
        return value

    @field_validator("port", mode="before")
    @classmethod
    def _parse_port(cls, value: object) -> object:
        if value is None or value == "":
            return 8000
        return value

    @model_validator(mode="after")
    def _validate_webhook_settings(self) -> "Settings":
        if self.use_webhook:
            if not self.render_external_url:
                msg = "RENDER_EXTERNAL_URL is required when TELEGRAM_MODE=webhook"
                raise ValueError(msg)
            if not self.telegram_webhook_secret:
                msg = "TELEGRAM_WEBHOOK_SECRET is required when TELEGRAM_MODE=webhook"
                raise ValueError(msg)
        return self

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def webhook_url(self) -> str:
        """Full Telegram webhook URL derived from Render external URL."""
        if not self.render_external_url:
            msg = "RENDER_EXTERNAL_URL is not configured"
            raise ValueError(msg)
        return f"{self.render_external_url.rstrip('/')}{WEBHOOK_PATH}"

    @property
    def use_webhook(self) -> bool:
        """Whether the bot should run in webhook mode."""
        return self.telegram_mode == "webhook"


def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()  # type: ignore[call-arg]
