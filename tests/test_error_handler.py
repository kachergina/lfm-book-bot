"""Tests for ErrorHandlerMiddleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, Message, User

from bot.middlewares.error_handler import ErrorHandlerMiddleware


def _create_mock_message() -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = "test"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.answer = AsyncMock()
    return message


def _create_mock_callback() -> CallbackQuery:
    """Create a mock Telegram callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "test:data"
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456789
    return callback


class TestErrorHandlerMiddleware:
    """Tests for ErrorHandlerMiddleware."""

    @pytest.mark.asyncio
    async def test_handler_exception_sends_message_error(self):
        """Test that handler exception sends error to Message event."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_message()
        data = {}

        result = await middleware(failing_handler, event, data)

        assert result is None
        event.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handler_exception_sends_callback_error(self):
        """Test that handler exception sends error alert to CallbackQuery."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_callback()
        data = {}

        result = await middleware(failing_handler, event, data)

        assert result is None
        event.answer.assert_called_once()
        # Check that show_alert=True was passed
        call_kwargs = event.answer.call_args
        assert call_kwargs.kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_handler_success_passes_through(self):
        """Test that successful handler result is passed through."""
        middleware = ErrorHandlerMiddleware()

        async def success_handler(event, data):
            return "success"

        event = _create_mock_message()
        data = {}

        result = await middleware(success_handler, event, data)

        assert result == "success"
        event.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_answer_failure_is_silent(self):
        """Test that failure to send callback answer doesn't raise."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_callback()
        event.answer = AsyncMock(side_effect=Exception("Telegram API error"))
        data = {}

        # Should not raise
        result = await middleware(failing_handler, event, data)
        assert result is None

    @pytest.mark.asyncio
    async def test_message_answer_failure_is_silent(self):
        """Test that failure to send message answer doesn't raise."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_message()
        event.answer = AsyncMock(side_effect=Exception("Telegram API error"))
        data = {}

        # Should not raise
        result = await middleware(failing_handler, event, data)
        assert result is None

    @pytest.mark.asyncio
    async def test_admin_notification_attempted(self):
        """Test that admin notification is attempted on error."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_message()
        data = {}

        with patch.object(
            ErrorHandlerMiddleware, "_notify_admins", new_callable=AsyncMock
        ) as mock_notify:
            await middleware(failing_handler, event, data)
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_admin_notification_failure_is_silent(self):
        """Test that admin notification failure doesn't raise."""
        middleware = ErrorHandlerMiddleware()

        async def failing_handler(event, data):
            raise ValueError("Test error")

        event = _create_mock_message()
        data = {}

        with patch.object(
            ErrorHandlerMiddleware, "_notify_admins", new_callable=AsyncMock
        ) as mock_notify:
            mock_notify.side_effect = Exception("Notification error")
            # Should not raise
            result = await middleware(failing_handler, event, data)
            assert result is None

    def test_extract_user_id_from_message(self):
        """Test user ID extraction from Message."""
        event = _create_mock_message()
        user_id = ErrorHandlerMiddleware._extract_user_id(event)
        assert user_id == 123456789

    def test_extract_user_id_from_callback(self):
        """Test user ID extraction from CallbackQuery."""
        event = _create_mock_callback()
        user_id = ErrorHandlerMiddleware._extract_user_id(event)
        assert user_id == 123456789

    def test_extract_user_id_no_from_user(self):
        """Test user ID extraction when from_user is None."""
        event = MagicMock(spec=Message)
        event.from_user = None
        user_id = ErrorHandlerMiddleware._extract_user_id(event)
        assert user_id is None
