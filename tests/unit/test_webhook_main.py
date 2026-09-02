"""Tests for webhook lifecycle in main module."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot, Dispatcher

from bot.config import Settings
from bot.main import (
    configure_dispatcher,
    delete_telegram_webhook,
    main,
    register_telegram_webhook,
    run_webhook,
)


def _mock_bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    return bot


def _webhook_env(**overrides: str) -> dict[str, str]:
    env = {
        "TELEGRAM_BOT_TOKEN": "test-token",
        "TELEGRAM_MODE": "webhook",
        "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com",
        "TELEGRAM_WEBHOOK_SECRET": "secret",
    }
    env.update(overrides)
    return env


class TestWebhookConfig:
    """Tests for webhook-related settings."""

    def test_webhook_url_from_render_external_url(self) -> None:
        """Webhook URL is built from RENDER_EXTERNAL_URL."""
        with patch.dict(os.environ, _webhook_env(), clear=False):
            settings = Settings()
            assert settings.webhook_url == "https://books-bot.onrender.com/telegram/webhook"

    def test_use_webhook_follows_telegram_mode(self) -> None:
        """TELEGRAM_MODE controls polling vs webhook, not ENVIRONMENT alone."""
        polling_env = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_MODE": "polling",
            "ENVIRONMENT": "production",
        }
        with patch.dict(os.environ, polling_env, clear=False):
            assert Settings().use_webhook is False

        with patch.dict(os.environ, _webhook_env(ENVIRONMENT="development"), clear=False):
            assert Settings().use_webhook is True

    def test_webhook_mode_requires_render_external_url(self) -> None:
        """Webhook mode without RENDER_EXTERNAL_URL fails validation."""
        env_vars = _webhook_env()
        del env_vars["RENDER_EXTERNAL_URL"]
        with (
            patch.dict(os.environ, env_vars, clear=False),
            pytest.raises(ValueError, match="RENDER_EXTERNAL_URL"),
        ):
            Settings()

    def test_webhook_mode_requires_webhook_secret(self) -> None:
        """Webhook mode without TELEGRAM_WEBHOOK_SECRET fails validation."""
        env_vars = _webhook_env()
        del env_vars["TELEGRAM_WEBHOOK_SECRET"]
        with (
            patch.dict(os.environ, env_vars, clear=False),
            pytest.raises(ValueError, match="TELEGRAM_WEBHOOK_SECRET"),
        ):
            Settings()

    def test_invalid_telegram_mode(self) -> None:
        """Unknown TELEGRAM_MODE values are rejected."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_MODE": "invalid",
        }
        with (
            patch.dict(os.environ, env_vars, clear=False),
            pytest.raises(ValueError, match="TELEGRAM_MODE"),
        ):
            Settings()

    def test_port_from_env(self) -> None:
        """PORT env var is parsed as integer."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "PORT": "10000",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            assert Settings().port == 10000


class TestWebhookLifecycle:
    """Tests for Telegram webhook registration."""

    @pytest.mark.asyncio
    async def test_register_telegram_webhook(self) -> None:
        """Webhook startup registers Telegram webhook with secret."""
        bot = AsyncMock(spec=Bot)
        with patch.dict(os.environ, _webhook_env(TELEGRAM_WEBHOOK_SECRET="my-secret"), clear=False):
            await register_telegram_webhook(bot)
            bot.set_webhook.assert_awaited_once_with(
                url="https://books-bot.onrender.com/telegram/webhook",
                secret_token="my-secret",
                drop_pending_updates=False,
            )

    @pytest.mark.asyncio
    async def test_delete_telegram_webhook(self) -> None:
        """Shutdown removes Telegram webhook."""
        bot = AsyncMock(spec=Bot)
        await delete_telegram_webhook(bot)
        bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=False)


class TestConfigureDispatcher:
    """Tests for dispatcher lifecycle configuration."""

    def test_webhook_mode_registers_webhook_handlers(self) -> None:
        """Webhook mode adds Telegram webhook startup/shutdown handlers."""
        dp = Dispatcher()
        configure_dispatcher(dp, use_webhook=True)
        handler_names = [handler.callback.__name__ for handler in dp.startup.handlers]
        assert "on_startup" in handler_names
        assert "register_telegram_webhook" in handler_names

    def test_polling_mode_skips_webhook_handlers(self) -> None:
        """Polling mode does not register Telegram webhook handlers."""
        dp = Dispatcher()
        configure_dispatcher(dp, use_webhook=False)
        handler_names = [handler.callback.__name__ for handler in dp.startup.handlers]
        assert "register_telegram_webhook" not in handler_names


class TestMainRunMode:
    """Tests for polling vs webhook entrypoint selection."""

    @pytest.mark.asyncio
    async def test_main_uses_polling_when_telegram_mode_polling(self) -> None:
        """TELEGRAM_MODE=polling starts long polling."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "TELEGRAM_MODE": "polling",
        }
        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("bot.main.run_polling", new_callable=AsyncMock) as mock_polling,
            patch("bot.main.run_webhook", new_callable=AsyncMock) as mock_webhook,
            patch("bot.main.create_bot", return_value=_mock_bot()),
            patch("bot.main.build_dispatcher", return_value=Dispatcher()),
        ):
            await main()
            mock_polling.assert_awaited_once()
            mock_webhook.assert_not_called()

    @pytest.mark.asyncio
    async def test_main_uses_webhook_when_telegram_mode_webhook(self) -> None:
        """TELEGRAM_MODE=webhook starts the aiohttp server."""
        with (
            patch.dict(os.environ, _webhook_env(), clear=False),
            patch("bot.main.run_polling", new_callable=AsyncMock) as mock_polling,
            patch("bot.main.run_webhook", new_callable=AsyncMock) as mock_webhook,
            patch("bot.main.create_bot", return_value=_mock_bot()),
            patch("bot.main.build_dispatcher", return_value=Dispatcher()),
        ):
            await main()
            mock_webhook.assert_awaited_once()
            mock_polling.assert_not_called()


class TestRunWebhookStartupOrder:
    """Regression tests for Render port detection."""

    @pytest.mark.asyncio
    async def test_run_webhook_binds_port_before_emit_startup(self) -> None:
        """HTTP port must open before DB/webhook startup for Render health checks."""
        bot = _mock_bot()
        dp = Dispatcher()
        configure_dispatcher(dp, use_webhook=True)
        settings = Settings(
            telegram_bot_token="test-token",
            telegram_mode="webhook",
            render_external_url="https://books-bot.onrender.com",
            telegram_webhook_secret="secret",
            port=8080,
        )
        events: list[str] = []

        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock(side_effect=lambda: events.append("runner_setup"))
        mock_runner.cleanup = AsyncMock()

        mock_site = MagicMock()
        mock_site.start = AsyncMock(side_effect=lambda: events.append("port_open"))

        async def tracked_emit_startup(**kwargs: object) -> None:
            events.append("startup")

        stop_event = asyncio.Event()
        stop_event.set()

        with (
            patch("bot.main.create_web_app", return_value=MagicMock()),
            patch("bot.main.web.AppRunner", return_value=mock_runner),
            patch("bot.main.web.TCPSite", return_value=mock_site),
            patch.object(dp, "emit_startup", side_effect=tracked_emit_startup),
            patch.object(dp, "emit_shutdown", new_callable=AsyncMock),
            patch("bot.main.asyncio.Event", return_value=stop_event),
        ):
            await run_webhook(bot, dp, settings)

        assert events == ["runner_setup", "port_open", "startup"]
        mock_site.start.assert_awaited_once_with()
        mock_runner.cleanup.assert_awaited_once()
