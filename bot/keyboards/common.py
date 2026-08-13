"""Common keyboards for the bot."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot.locale import fr


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get the main menu keyboard.

    Returns:
        Main menu keyboard with navigation buttons.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=fr.BTN_BUY_BOOK)],
            [KeyboardButton(text=fr.BTN_SELL_BOOK)],
            [
                KeyboardButton(text=fr.BTN_MY_LISTINGS),
                KeyboardButton(text=fr.BTN_HELP),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Get a simple back button keyboard.

    Returns:
        Keyboard with back button.
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Retour")]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Get inline main menu keyboard.

    Returns:
        Inline keyboard for main menu navigation.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=fr.BTN_BUY_BOOK, callback_data="menu:buy")],
            [InlineKeyboardButton(text=fr.BTN_SELL_BOOK, callback_data="menu:sell")],
            [
                InlineKeyboardButton(
                    text=fr.BTN_MY_LISTINGS,
                    callback_data="menu:listings",
                ),
                InlineKeyboardButton(text=fr.BTN_HELP, callback_data="menu:help"),
            ],
        ],
    )
