"""Tests for configuration management."""

import os
from unittest.mock import patch

from bot.config import Settings, get_settings, normalize_database_url


class TestSettings:
    """Tests for Settings class."""

    def test_settings_from_env(self) -> None:
        """Test loading settings from environment variables."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token-123",
            "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
            "ENVIRONMENT": "test",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.telegram_bot_token == "test-token-123"
            assert settings.database_url == "sqlite+aiosqlite:///./test.db"
            assert settings.environment == "test"

    def test_settings_defaults(self) -> None:
        """Test default settings values."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "development",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.environment == "development"
            assert settings.log_level == "INFO"
            assert settings.max_listings_per_user == 50
            assert settings.listing_expiry_days == 180

    def test_is_production_property(self) -> None:
        """Test is_production property."""
        env_vars = {"TELEGRAM_BOT_TOKEN": "test-token"}
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            settings.environment = "production"
            assert settings.is_production is True
            settings.environment = "development"
            assert settings.is_production is False


class TestNormalizeDatabaseUrl:
    """Tests for PostgreSQL URL normalization."""

    def test_postgresql_scheme(self) -> None:
        """postgresql:// is converted to postgresql+asyncpg://."""
        assert (
            normalize_database_url("postgresql://user:pass@host:5432/db")
            == "postgresql+asyncpg://user:pass@host:5432/db"
        )

    def test_postgres_scheme(self) -> None:
        """postgres:// is converted to postgresql+asyncpg://."""
        assert (
            normalize_database_url("postgres://user:pass@host:5432/db")
            == "postgresql+asyncpg://user:pass@host:5432/db"
        )

    def test_asyncpg_url_unchanged(self) -> None:
        """Already-async URLs are not modified."""
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        assert normalize_database_url(url) == url

    def test_sqlite_url_unchanged(self) -> None:
        """SQLite development URLs are not modified."""
        url = "sqlite+aiosqlite:///./data/bot.db"
        assert normalize_database_url(url) == url

    def test_settings_normalizes_render_postgres_url(self) -> None:
        """Settings loads Render-style postgres:// URLs as asyncpg."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "DATABASE_URL": "postgres://user:pass@host:5432/db",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/db"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        env_vars = {"TELEGRAM_BOT_TOKEN": "test-token"}
        with patch.dict(os.environ, env_vars, clear=False):
            settings = get_settings()
            assert isinstance(settings, Settings)
