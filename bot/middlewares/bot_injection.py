"""Bot injection middleware for aiogram."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject


class BotMiddleware(BaseMiddleware):
    """Middleware to inject the Bot instance into handler data."""

    def __init__(self, bot: Bot) -> None:
        """Initialize with a Bot instance.

        Args:
            bot: Aiogram Bot instance.
        """
        self.bot = bot

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process handler with bot injection.

        Args:
            handler: Next handler to call.
            event: Telegram event.
            data: Handler data.

        Returns:
            Handler result.
        """
        data["bot"] = self.bot
        return await handler(event, data)
