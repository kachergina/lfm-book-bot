"""aiohttp web server for Render webhook deployment."""

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.constants import WEBHOOK_PATH


async def health_handler(_request: web.Request) -> web.Response:
    """Health check endpoint for Render."""
    return web.json_response({"status": "ok"})


def create_web_app(
    bot: Bot,
    dp: Dispatcher,
    *,
    secret_token: str,
) -> web.Application:
    """Build aiohttp application with health and Telegram webhook routes."""
    app = web.Application()
    app.router.add_get("/health", health_handler)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=secret_token,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app
