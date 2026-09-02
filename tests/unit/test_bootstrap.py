"""Tests for shared bot bootstrap."""

import inspect

from bot.bootstrap import build_dispatcher, create_bot


def test_middleware_registered_in_bootstrap() -> None:
    """DatabaseSessionMiddleware is registered when building the dispatcher."""
    source = inspect.getsource(build_dispatcher)
    assert "DatabaseSessionMiddleware" in source
    assert "BannedUserMiddleware" in source
    assert "ErrorHandlerMiddleware" in source


def test_routers_registered_in_bootstrap() -> None:
    """All handler routers are included in the dispatcher."""
    source = inspect.getsource(build_dispatcher)
    assert "start_router" in source
    assert "admin_router" in source
    assert "catalog_router" in source
    assert "sell_router" in source
    assert "listings_router" in source


def test_create_bot_uses_html_parse_mode() -> None:
    """Bot is created with HTML parse mode defaults."""
    source = inspect.getsource(create_bot)
    assert "ParseMode.HTML" in source
