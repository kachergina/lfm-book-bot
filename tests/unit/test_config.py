"""Tests for configuration management."""

import os
import ssl
from unittest.mock import patch

from bot.config import Settings, get_settings, normalize_database_url, prepare_asyncpg_url


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


class TestPrepareAsyncpgUrl:
    """Regression tests for Neon/libpq URL params with asyncpg."""

    _neon_base = (
        "postgresql://user:pass@ep-example-pooler.us-east-1.aws.neon.tech/neondb"
    )

    def test_neon_sslmode_require_stripped_and_mapped(self) -> None:
        """sslmode=require must not reach asyncpg.connect() as sslmode."""
        url, connect_args = prepare_asyncpg_url(f"{self._neon_base}?sslmode=require")
        assert url == (
            "postgresql+asyncpg://user:pass@ep-example-pooler.us-east-1.aws.neon.tech/neondb"
        )
        assert connect_args == {"ssl": True}
        assert "sslmode" not in url

    def test_sslmode_disable(self) -> None:
        """sslmode=disable maps to ssl=False."""
        _, connect_args = prepare_asyncpg_url(
            "postgresql://user:pass@host:5432/db?sslmode=disable"
        )
        assert connect_args == {"ssl": False}

    def test_sslmode_verify_full_uses_ssl_context(self) -> None:
        """sslmode=verify-full maps to an SSLContext."""
        _, connect_args = prepare_asyncpg_url(
            "postgresql://user:pass@host:5432/db?sslmode=verify-full"
        )
        assert isinstance(connect_args["ssl"], ssl.SSLContext)

    def test_libpq_only_params_stripped(self) -> None:
        """Unsupported libpq params are removed from the engine URL."""
        raw = (
            "postgresql://user:pass@host:5432/db"
            "?sslmode=require&channel_binding=require&sslrootcert=system"
        )
        url, connect_args = prepare_asyncpg_url(raw)
        assert "sslmode" not in url
        assert "channel_binding" not in url
        assert "sslrootcert" not in url
        assert connect_args == {"ssl": True}

    def test_other_query_params_preserved(self) -> None:
        """Non-libpq query params unrelated to SSL are kept."""
        url, connect_args = prepare_asyncpg_url(
            "postgresql://user:pass@host:5432/db?sslmode=require&application_name=books_bot"
        )
        assert url.endswith("application_name=books_bot")
        assert connect_args == {"ssl": True}

    def test_sqlite_unchanged(self) -> None:
        """Local SQLite URLs are not modified."""
        url = "sqlite+aiosqlite:///./data/bot.db"
        assert prepare_asyncpg_url(url) == (url, {})

    def test_settings_neon_database_url(self) -> None:
        """Settings accepts Neon DATABASE_URL with sslmode=require."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "DATABASE_URL": f"{self._neon_base}?sslmode=require",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.database_url == f"{self._neon_base.replace('postgresql://', 'postgresql+asyncpg://')}?sslmode=require"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self) -> None:
        """Test that get_settings returns a Settings instance."""
        env_vars = {"TELEGRAM_BOT_TOKEN": "test-token"}
        with patch.dict(os.environ, env_vars, clear=False):
            settings = get_settings()
            assert isinstance(settings, Settings)
