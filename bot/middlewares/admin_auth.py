"""Admin authorization middleware for the bot."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.config import get_settings
from bot.locale import fr

logger = logging.getLogger(__name__)


class AdminAuthMiddleware(BaseMiddleware):
    """Middleware to restrict admin-only handlers to authorized admins.

    This middleware checks the user's Telegram ID against BOT_ADMIN_IDS.
    Non-admin users receive a French error message and the handler is not called.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process handler with admin authorization check.

        Args:
            handler: Next handler to call.
            event: Telegram event.
            data: Handler data.

        Returns:
            Handler result or None if not authorized.
        """
        settings = get_settings()
        admin_ids = settings.bot_admin_ids

        user_id = self._extract_user_id(event)
        if user_id is None or user_id not in admin_ids:
            logger.warning(
                "admin_access_denied user_id=%s",
                user_id,
            )
            if isinstance(event, CallbackQuery):
                await event.answer(fr.MSG_NOT_ADMIN, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(fr.MSG_NOT_ADMIN)
            return None

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
