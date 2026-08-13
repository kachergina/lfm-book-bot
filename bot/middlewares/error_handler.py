"""Error handling middleware for the bot."""

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.locale import fr

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware to handle errors gracefully.

    Catches unhandled exceptions in handlers, logs them, and sends
    a user-friendly French error message. For CallbackQuery events,
    the error is shown as an alert. For Message events, a plain
    text reply is sent.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process handler with error handling.

        Args:
            handler: Next handler to call.
            event: Telegram event.
            data: Handler data.

        Returns:
            Handler result or None on error.
        """
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Unhandled error in handler")

            user_id = self._extract_user_id(event)

            logger.exception(
                "handler_error user_id=%s event_type=%s",
                user_id,
                type(event).__name__,
            )

            if isinstance(event, CallbackQuery):
                try:
                    await event.answer(fr.MSG_SOMETHING_WENT_WRONG, show_alert=True)
                except Exception:
                    logger.exception("Failed to send callback error answer")
            elif isinstance(event, Message):
                try:
                    await event.answer(fr.MSG_SOMETHING_WENT_WRONG)
                except Exception:
                    logger.exception("Failed to send message error answer")

            try:
                await self._notify_admins(data, user_id)
            except Exception:
                logger.exception("Failed to notify admins about handler error")
            return None

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

    @staticmethod
    async def _notify_admins(data: dict[str, Any], user_id: int | None) -> None:
        """Attempt to notify admins about the error.

        This is best-effort: if the bot or session isn't available,
        the admin notification is silently skipped.

        Args:
            data: Handler data (may contain 'bot' and 'session').
            user_id: User ID associated with the error.
        """
        bot = data.get("bot")
        session = data.get("session")
        if bot is None or session is None:
            return

        try:
            from bot.services.notification import NotificationService

            notification_service = NotificationService(bot, session)
            await notification_service.notify_admin_error(
                error=Exception("Unhandled handler error"),
                user_id=user_id,
            )
        except Exception:
            logger.exception("Failed to send admin error notification")
