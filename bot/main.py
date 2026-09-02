"""Application entry point for the School Books Marketplace Bot."""

import asyncio
import contextlib
import logging
import signal
import sys

from aiogram import Bot, Dispatcher
from aiohttp import web

from bot.bootstrap import build_dispatcher, create_bot
from bot.config import Settings, get_settings
from bot.database import close_db, get_session, init_db, init_engine
from bot.utils.helpers import format_price
from bot.web.server import create_web_app

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


async def register_telegram_webhook(bot: Bot) -> None:
    """Register Telegram webhook URL for production."""
    settings = get_settings()
    logger = logging.getLogger(__name__)
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.telegram_webhook_secret,
        drop_pending_updates=False,
    )
    logger.info("Telegram webhook registered at %s", settings.webhook_url)


async def delete_telegram_webhook(bot: Bot) -> None:
    """Remove Telegram webhook on shutdown."""
    logger = logging.getLogger(__name__)
    await bot.delete_webhook(drop_pending_updates=False)
    logger.info("Telegram webhook removed")


def configure_dispatcher(dp: Dispatcher, *, use_webhook: bool) -> None:
    """Register lifecycle handlers on the dispatcher."""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    if use_webhook:
        dp.startup.register(register_telegram_webhook)
        dp.shutdown.register(delete_telegram_webhook)


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    """Run the bot in long-polling mode (local development)."""
    logger = logging.getLogger(__name__)
    logger.info("Bot starting polling...")
    await dp.start_polling(bot)


async def run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    """Run the bot behind an aiohttp webhook server (Render production)."""
    logger = logging.getLogger(__name__)
    app = create_web_app(
        bot,
        dp,
        secret_token=settings.telegram_webhook_secret or "",
        register_lifecycle=False,
    )
    runner = web.AppRunner(app, handle_signals=False)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.port)
    await site.start()
    logger.info("HTTP server listening on 0.0.0.0:%s", settings.port)

    stop_event = asyncio.Event()

    def request_shutdown() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig_name in ("SIGINT", "SIGTERM"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            with contextlib.suppress(NotImplementedError):
                loop.add_signal_handler(sig, request_shutdown)

    try:
        await dp.emit_startup(bot=bot, app=app, dispatcher=dp)
        logger.info("Application startup complete")
        await stop_event.wait()
    finally:
        await dp.emit_shutdown(bot=bot, app=app, dispatcher=dp)
        await runner.cleanup()


async def main() -> None:
    """Main entry point."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger = logging.getLogger(__name__)
    bot = create_bot(settings)
    dp = build_dispatcher(bot)
    configure_dispatcher(dp, use_webhook=settings.use_webhook)

    try:
        if settings.use_webhook:
            await run_webhook(bot, dp, settings)
        else:
            await run_polling(bot, dp)
    except Exception as e:
        logger.critical("Fatal error: %s", e)
        raise
    finally:
        if not settings.use_webhook:
            await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
