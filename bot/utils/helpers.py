"""Shared helper functions for handlers."""

from decimal import Decimal

from aiogram.types import CallbackQuery, InlineKeyboardMarkup


async def edit_message(
    callback: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Safely edit callback message.

    Args:
        callback: Telegram callback.
        text: New message text.
        reply_markup: Optional reply markup.
    """
    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(text, reply_markup=reply_markup)


def format_price(price: Decimal) -> str:
    """Format price as whole rubles without decimal zeros.

    Args:
        price: Price as Decimal.

    Returns:
        Formatted price string, e.g. "1500".
    """
    return f"{int(price)}"
