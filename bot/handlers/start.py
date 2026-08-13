"""Start and help command handlers."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.locale import fr

logger = logging.getLogger(__name__)

router = Router()


async def _send_help(message: Message) -> None:
    """Send help message.

    Args:
        message: Telegram message.
    """
    await message.answer(fr.HELP_MESSAGE)


@router.message(F.text == fr.BTN_HELP)
async def cmd_help_button(message: Message) -> None:
    """Handle help button.

    Args:
        message: Telegram message.
    """
    await _send_help(message)


@router.message(Command("help"))
async def cmd_help_command(message: Message) -> None:
    """Handle /help command.

    Args:
        message: Telegram message.
    """
    await _send_help(message)
