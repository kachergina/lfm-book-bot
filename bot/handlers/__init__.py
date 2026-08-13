"""Handlers package."""

from bot.handlers.admin import router as admin_router
from bot.handlers.catalog import router as catalog_router
from bot.handlers.listings import router as listings_router
from bot.handlers.sell import router as sell_router
from bot.handlers.start import router as start_router

__all__ = [
    "start_router",
    "catalog_router",
    "sell_router",
    "listings_router",
    "admin_router",
]
