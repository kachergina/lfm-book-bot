"""Banned user restriction middleware for the bot."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.locale import fr

logger = logging.getLogger(__name__)


class BannedUserMiddleware(BaseMiddleware):
    """Middleware to restrict banned users from using marketplace functionality.

    When a user is banned, they cannot access any marketplace features.
    This middleware checks the user's ban status via the database.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process handler with banned user check.

        Args:
            handler: Next handler to call.
            event: Telegram event.
            data: Handler data.

        Returns:
            Handler result or None if user is banned.
        """
        user_id = self._extract_user_id(event)
        if user_id is None:
            return await handler(event, data)

        # Check ban status from database via repository
        session = data.get("session")
        if session is not None:
            try:
                from bot.database.repository import UserRepository

                user_repo = UserRepository(session)
                user = await user_repo.get_by_telegram_id(user_id)
                if user is not None and user.is_banned:
                    logger.info("banned_user_attempt user_id=%s", user_id)
                    if isinstance(event, CallbackQuery):
                        await event.answer(fr.MSG_BANNED, show_alert=True)
                    elif isinstance(event, Message):
                        await event.answer(fr.MSG_BANNED)
                    return None
            except Exception:
                logger.exception("Failed to check ban status for user_id=%s", user_id)

        return await handler(event, data)

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        """Extract user ID from a Telegram event.

        Args:
            event: Telegram event.

        Returns:
            User ID or None.
        """
        if hasattr(event, "from_user") and event.from_user is not None:
            user_id: int = event.from_user.id
            return user_id
        return None
