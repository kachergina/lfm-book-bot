"""Shared bot and dispatcher setup."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Settings
from bot.handlers import admin_router, catalog_router, listings_router, sell_router, start_router
from bot.middlewares import (
    BannedUserMiddleware,
    BotMiddleware,
    DatabaseSessionMiddleware,
    ErrorHandlerMiddleware,
)


def create_bot(settings: Settings) -> Bot:
    """Create a configured Bot instance."""
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher(bot: Bot) -> Dispatcher:
    """Create dispatcher with middlewares and routers."""
    dp = Dispatcher()

    dp.message.middleware(BotMiddleware(bot))
    dp.message.middleware(DatabaseSessionMiddleware())
    dp.message.middleware(BannedUserMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(BotMiddleware(bot))
    dp.callback_query.middleware(DatabaseSessionMiddleware())
    dp.callback_query.middleware(BannedUserMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(catalog_router)
    dp.include_router(sell_router)
    dp.include_router(listings_router)

    return dp
