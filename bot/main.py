"""Application entry point for the School Books Marketplace Bot."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import get_settings
from bot.database import close_db, get_session, init_db, init_engine
from bot.handlers import admin_router, catalog_router, listings_router, sell_router, start_router
from bot.middlewares import (
    BannedUserMiddleware,
    BotMiddleware,
    DatabaseSessionMiddleware,
    ErrorHandlerMiddleware,
)
from bot.utils.helpers import format_price

EXPIRY_CHECK_INTERVAL_SECONDS = 3600  # Check every hour


def setup_logging(log_level: str) -> None:
    """Configure application logging.

    Args:
        log_level: Logging level string.
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # Suppress noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.INFO)


_expiry_task: asyncio.Task[None] | None = None
_shutdown_event = asyncio.Event()


async def _run_expiry_check() -> None:
    """Run a single expiry check against the database."""
    logger = logging.getLogger(__name__)
    try:
        async for session in get_session():
            from bot.services.listing import ListingService

            service = ListingService(session)
            expired = await service.expire_listings()
            if expired:
                logger.info("Expired %d listings automatically", len(expired))

                # Notify expired sellers
                from bot.services.notification import NotificationService

                settings = get_settings()
                bot = Bot(token=settings.telegram_bot_token)
                try:
                    notif_service = NotificationService(bot, session)
                    for listing in expired:
                        if listing.seller:
                            from bot.locale import fr

                            book_title = listing.book.title if listing.book else "Livre inconnu"
                            text = fr.ADMIN_EXPIRY_NOTIFICATION.format(
                                title=book_title,
                                price=format_price(listing.price),
                            )
                            await notif_service._send_message(
                                chat_id=listing.seller.telegram_id,
                                text=text,
                                context=f"listing_expired(listing={listing.id})",
                            )
                except Exception:
                    logger.exception("Failed to notify expired listing sellers")
                finally:
                    await bot.session.close()
    except Exception:
        logger.exception("Expiry check failed")


async def _expiry_loop() -> None:
    """Periodically check for expired listings until shutdown."""
    logger = logging.getLogger(__name__)
    logger.info("Expiry loop started (interval=%ds)", EXPIRY_CHECK_INTERVAL_SECONDS)
    while not _shutdown_event.is_set():
        try:
            await asyncio.wait_for(
                _shutdown_event.wait(),
                timeout=EXPIRY_CHECK_INTERVAL_SECONDS,
            )
            break  # Shutdown requested during wait
        except TimeoutError:
            pass
        await _run_expiry_check()
    logger.info("Expiry loop stopped")


async def on_startup() -> None:
    """Handle application startup."""
    global _expiry_task  # noqa: PLW0603

    logger = logging.getLogger(__name__)
    logger.info("Starting School Books Marketplace Bot...")

    settings = get_settings()

    # Initialize database engine
    init_engine(
        database_url=settings.database_url,
        echo=settings.environment == "development",
    )
    logger.info("Database engine initialized")

    # Initialize database tables
    await init_db()
    logger.info("Database tables created")

    logger.info(
        "Configuration loaded",
        extra={"environment": settings.environment},
    )

    # Run initial expiry check and start periodic loop
    await _run_expiry_check()
    _expiry_task = asyncio.create_task(_expiry_loop())


async def on_shutdown() -> None:
    """Handle application shutdown."""
    global _expiry_task  # noqa: PLW0603

    logger = logging.getLogger(__name__)
    logger.info("Shutting down...")

    # Signal expiry loop to stop and wait for it
    _shutdown_event.set()
    if _expiry_task is not None:
        try:
            await asyncio.wait_for(_expiry_task, timeout=5)
        except TimeoutError:
            _expiry_task.cancel()
        _expiry_task = None

    await close_db()
    logger.info("Database connections closed")


async def main() -> None:
    """Main entry point."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)

    # Create bot with default properties
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Create dispatcher
    dp = Dispatcher()

    # Include middlewares
    dp.message.middleware(BotMiddleware(bot))
    dp.message.middleware(DatabaseSessionMiddleware())
    dp.message.middleware(BannedUserMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(BotMiddleware(bot))
    dp.callback_query.middleware(DatabaseSessionMiddleware())
    dp.callback_query.middleware(BannedUserMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

    # Include routers
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(catalog_router)
    dp.include_router(sell_router)
    dp.include_router(listings_router)

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        # Start polling
        logger.info("Bot starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical("Fatal error: %s", e)
        raise
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
