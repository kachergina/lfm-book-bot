"""Tests for keyboards."""

from bot.keyboards.common import (
    get_back_keyboard,
    get_main_menu_inline_keyboard,
    get_main_menu_keyboard,
)
from bot.locale import fr


class TestKeyboards:
    """Tests for keyboard functions."""

    def test_main_menu_keyboard(self) -> None:
        """Test main menu keyboard structure."""
        keyboard = get_main_menu_keyboard()
        assert keyboard is not None
        assert len(keyboard.keyboard) == 3
        # Check first row has buy button
        assert keyboard.keyboard[0][0].text == fr.BTN_BUY_BOOK
        # Check second row has sell button
        assert keyboard.keyboard[1][0].text == fr.BTN_SELL_BOOK
        # Check third row has listings and help
        assert keyboard.keyboard[2][0].text == fr.BTN_MY_LISTINGS
        assert keyboard.keyboard[2][1].text == fr.BTN_HELP

    def test_back_keyboard(self) -> None:
        """Test back keyboard structure."""
        keyboard = get_back_keyboard()
        assert keyboard is not None
        assert len(keyboard.keyboard) == 1
        assert keyboard.keyboard[0][0].text == "⬅️ Retour"

    def test_main_menu_inline_keyboard(self) -> None:
        """Test main menu inline keyboard structure."""
        keyboard = get_main_menu_inline_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 3
        # Check callbacks
        assert keyboard.inline_keyboard[0][0].callback_data == "menu:buy"
        assert keyboard.inline_keyboard[1][0].callback_data == "menu:sell"
        assert keyboard.inline_keyboard[2][0].callback_data == "menu:listings"
        assert keyboard.inline_keyboard[2][1].callback_data == "menu:help"
