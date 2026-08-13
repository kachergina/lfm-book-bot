"""Tests for database session middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message
from aiogram.types import User as AiogramUser

from bot.middlewares.db_session import DatabaseSessionMiddleware


def _create_mock_message() -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=AiogramUser)
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "fr"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_database_session_middleware_injects_session(db_session):
    """Test that DatabaseSessionMiddleware injects session into handler data."""
    middleware = DatabaseSessionMiddleware()
    handler = AsyncMock()
    event = MagicMock()
    data = {}

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=db_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.database.base.async_session_factory", mock_factory):
        await middleware(handler, event, data)

        assert "session" in data
        assert data["session"] is db_session
        handler.assert_called_once_with(event, data)


@pytest.mark.asyncio
async def test_start_handler_receives_session(db_session):
    """Test that /start handler receives session from middleware."""
    from bot.handlers.catalog import cmd_start_buy_flow

    message = _create_mock_message()
    state = AsyncMock()

    # Mock the repository calls
    with patch("bot.database.repository.UserRepository") as mock_user_repo:
        mock_user_instance = AsyncMock()
        mock_user_instance.get_by_telegram_id = AsyncMock(return_value=None)
        mock_user_instance.create = AsyncMock(return_value=MagicMock(id=1))
        mock_user_repo.return_value = mock_user_instance

        with patch("bot.database.repository.AcademicYearRepository") as mock_year_repo:
            mock_year_instance = AsyncMock()
            mock_academic_year = MagicMock()
            mock_academic_year.name = "2025-2026"
            mock_year_instance.get_current = AsyncMock(return_value=mock_academic_year)
            mock_year_repo.return_value = mock_year_instance

            await cmd_start_buy_flow(message, state, db_session)

            message.answer.assert_called_once()
            call_args = message.answer.call_args
            assert "Bienvenue" in call_args[0][0]
            assert "2025-2026" in call_args[0][0]


def test_middleware_registered_in_main():
    """Test that DatabaseSessionMiddleware is registered in main.py."""
    import inspect

    from bot.main import main

    source = inspect.getsource(main)
    assert "DatabaseSessionMiddleware" in source
