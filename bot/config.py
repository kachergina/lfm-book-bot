"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
