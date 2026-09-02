"""Tests for aiohttp webhook server."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot, Dispatcher
from aiohttp.test_utils import TestClient, TestServer

from bot.constants import WEBHOOK_PATH
from bot.web.server import create_web_app, health_handler


def _mock_bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    bot.session.json_loads = json.loads
    bot.session.json_dumps = json.dumps
    return bot


@pytest.mark.asyncio
async def test_health_handler_returns_ok() -> None:
    """GET /health should return status ok."""
    response = await health_handler(MagicMock())
    assert response.status == 200
    assert response.body == b'{"status": "ok"}'


@pytest.mark.asyncio
async def test_health_route() -> None:
    """Health endpoint is registered on the web app."""
    bot = _mock_bot()
    dp = Dispatcher()
    app = create_web_app(bot, dp, secret_token="test-secret")

    async with TestClient(TestServer(app)) as client:
        response = await client.get("/health")
        assert response.status == 200
        assert await response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_webhook_rejects_missing_secret() -> None:
    """POST /telegram/webhook without secret token returns 401."""
    bot = _mock_bot()
    dp = Dispatcher()
    app = create_web_app(bot, dp, secret_token="test-secret")

    async with TestClient(TestServer(app)) as client:
        response = await client.post(WEBHOOK_PATH, json={"update_id": 1})
        assert response.status == 401


@pytest.mark.asyncio
async def test_webhook_rejects_invalid_secret() -> None:
    """POST /telegram/webhook with wrong secret token returns 401."""
    bot = _mock_bot()
    dp = Dispatcher()
    app = create_web_app(bot, dp, secret_token="test-secret")

    async with TestClient(TestServer(app)) as client:
        response = await client.post(
            WEBHOOK_PATH,
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status == 401


@pytest.mark.asyncio
async def test_webhook_accepts_valid_secret() -> None:
    """POST /telegram/webhook with valid secret is accepted."""
    bot = _mock_bot()
    dp = Dispatcher()
    app = create_web_app(bot, dp, secret_token="test-secret")

    async with TestClient(TestServer(app)) as client:
        response = await client.post(
            WEBHOOK_PATH,
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        )
        assert response.status == 200
