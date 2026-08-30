"""Tests for database engine initialization."""

from unittest.mock import patch

import bot.database.base as db_base
from bot.database.base import init_engine


class TestInitEngine:
    """Tests for init_engine SSL handling."""

    def teardown_method(self) -> None:
        """Reset module-level engine state after each test."""
        db_base.engine = None
        db_base.async_session_factory = None

    def test_init_engine_passes_asyncpg_ssl_connect_args(self) -> None:
        """init_engine maps Neon sslmode to asyncpg connect_args."""
        neon_url = (
            "postgresql://user:pass@ep-example.neon.tech/neondb?sslmode=require"
        )
        with patch("bot.database.base.create_async_engine") as mock_create:
            init_engine(neon_url)
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args
            assert call_kwargs[0][0] == (
                "postgresql+asyncpg://user:pass@ep-example.neon.tech/neondb"
            )
            assert call_kwargs[1]["connect_args"] == {"ssl": True}
            assert "sslmode" not in call_kwargs[0][0]

    def test_init_engine_sqlite_no_connect_args(self) -> None:
        """SQLite init_engine does not pass PostgreSQL connect_args."""
        sqlite_url = "sqlite+aiosqlite:///:memory:"
        with patch("bot.database.base.create_async_engine") as mock_create:
            init_engine(sqlite_url)
            mock_create.assert_called_once_with(
                sqlite_url,
                echo=False,
                connect_args={},
            )
