"""Tests for start handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message
from aiogram.types import User as AiogramUser

from bot.handlers.catalog import cmd_start_buy_flow
from bot.handlers.start import cmd_help_button, cmd_help_command


@pytest.fixture
def mock_message() -> Message:
    """Create a mock Telegram message.

    Returns:
        Mocked message.
    """
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


class TestCmdStart:
    """Tests for /start command."""

    @pytest.mark.asyncio
    async def test_cmd_start_creates_new_user(self, mock_message: Message) -> None:
        """Test that /start creates a new user."""
        mock_session = AsyncMock()

        with patch("bot.database.repository.UserRepository") as mock_repo:
            mock_repo_instance = AsyncMock()
            mock_repo_instance.get_by_telegram_id = AsyncMock(return_value=None)
            mock_repo_instance.create = AsyncMock(return_value=MagicMock(id=1))
            mock_repo.return_value = mock_repo_instance

            with patch("bot.database.repository.AcademicYearRepository") as mock_year_repo:
                mock_year_repo_instance = AsyncMock()
                mock_academic_year = MagicMock()
                mock_academic_year.name = "2024-2025"
                mock_year_repo_instance.get_current = AsyncMock(return_value=mock_academic_year)
                mock_year_repo.return_value = mock_year_repo_instance

                state = AsyncMock()
                await cmd_start_buy_flow(mock_message, state, mock_session)

                mock_message.answer.assert_called_once()
                call_args = mock_message.answer.call_args
                assert "Bienvenue" in call_args[0][0]


class TestCmdHelp:
    """Tests for help command."""

    @pytest.mark.asyncio
    async def test_cmd_help(self, mock_message: Message) -> None:
        """Test help command."""
        await cmd_help_command(mock_message)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Aide" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_help_button_uses_same_message(self, mock_message: Message) -> None:
        """Test help button sends the same message as /help."""
        await cmd_help_button(mock_message)
        button_text = mock_message.answer.call_args[0][0]

        mock_message.answer.reset_mock()
        await cmd_help_command(mock_message)
        command_text = mock_message.answer.call_args[0][0]

        assert button_text == command_text
