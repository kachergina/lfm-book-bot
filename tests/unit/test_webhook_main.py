"""Tests for webhook lifecycle in main module."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot, Dispatcher

from bot.config import Settings
from bot.main import configure_dispatcher, delete_telegram_webhook, main, register_telegram_webhook


def _mock_bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.session = MagicMock()
    bot.session.close = AsyncMock()
    return bot


class TestWebhookConfig:
    """Tests for webhook-related settings."""

    def test_webhook_url_from_render_external_url(self) -> None:
        """Webhook URL is built from RENDER_EXTERNAL_URL."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com/",
            "TELEGRAM_WEBHOOK_SECRET": "secret",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.webhook_url == "https://books-bot.onrender.com/telegram/webhook"

    def test_use_webhook_only_in_production(self) -> None:
        """Development uses polling; production uses webhook."""
        dev_env = {"TELEGRAM_BOT_TOKEN": "test-token", "ENVIRONMENT": "development"}
        with patch.dict(os.environ, dev_env, clear=False):
            assert Settings().use_webhook is False

        prod_env = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com",
            "TELEGRAM_WEBHOOK_SECRET": "secret",
        }
        with patch.dict(os.environ, prod_env, clear=False):
            assert Settings().use_webhook is True

    def test_production_requires_render_external_url(self) -> None:
        """Production without RENDER_EXTERNAL_URL fails validation."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "TELEGRAM_WEBHOOK_SECRET": "secret",
        }
        with (
            patch.dict(os.environ, env_vars, clear=False),
            pytest.raises(ValueError, match="RENDER_EXTERNAL_URL"),
        ):
            Settings()

    def test_production_requires_webhook_secret(self) -> None:
        """Production without TELEGRAM_WEBHOOK_SECRET fails validation."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com",
        }
        with (
            patch.dict(os.environ, env_vars, clear=False),
            pytest.raises(ValueError, match="TELEGRAM_WEBHOOK_SECRET"),
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
        """Production startup registers webhook with secret."""
        bot = AsyncMock(spec=Bot)
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com",
            "TELEGRAM_WEBHOOK_SECRET": "my-secret",
        }
        with patch.dict(os.environ, env_vars, clear=False):
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
    async def test_main_uses_polling_in_development(self) -> None:
        """Development environment starts polling."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "development",
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
    async def test_main_uses_webhook_in_production(self) -> None:
        """Production environment starts webhook server."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "test-token",
            "ENVIRONMENT": "production",
            "RENDER_EXTERNAL_URL": "https://books-bot.onrender.com",
            "TELEGRAM_WEBHOOK_SECRET": "secret",
        }
        with (
            patch.dict(os.environ, env_vars, clear=False),
            patch("bot.main.run_polling", new_callable=AsyncMock) as mock_polling,
            patch("bot.main.run_webhook", new_callable=AsyncMock) as mock_webhook,
            patch("bot.main.create_bot", return_value=_mock_bot()),
            patch("bot.main.build_dispatcher", return_value=Dispatcher()),
        ):
            await main()
            mock_webhook.assert_awaited_once()
            mock_polling.assert_not_called()
