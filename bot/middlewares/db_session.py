"""Database session middleware for aiogram."""

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DatabaseSessionMiddleware(BaseMiddleware):
    """Middleware to inject database session into handlers."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Process handler with database session.

        Args:
            handler: Next handler to call.
            event: Telegram event.
            data: Handler data.

        Returns:
            Handler result.
        """
        from bot.database.base import async_session_factory

        if async_session_factory is None:
            raise RuntimeError("Database engine not initialized.")

        async with async_session_factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            else:
                await session.commit()
                return result
