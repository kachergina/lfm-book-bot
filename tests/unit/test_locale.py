"""Tests for French locale."""

from bot.locale import fr


class TestFrenchLocale:
    """Tests for French locale strings."""

    def test_welcome_message(self) -> None:
        """Test welcome message exists and is in French."""
        assert fr.WELCOME_MESSAGE is not None
        assert "Bienvenue" in fr.WELCOME_MESSAGE

    def test_main_menu_buttons(self) -> None:
        """Test main menu button texts exist and are in French."""
        assert fr.BTN_BUY_BOOK is not None
        assert "Acheter" in fr.BTN_BUY_BOOK
        assert fr.BTN_SELL_BOOK is not None
        assert "Met" in fr.BTN_SELL_BOOK
        assert fr.BTN_MY_LISTINGS is not None
        assert "annonces" in fr.BTN_MY_LISTINGS
        assert fr.BTN_HELP is not None
        assert "Aide" in fr.BTN_HELP

    def test_error_messages(self) -> None:
        """Test error messages exist and are in French."""
        assert fr.MSG_ERROR is not None
        assert fr.MSG_UNEXPECTED_ERROR is not None
        assert "erreur" in fr.MSG_UNEXPECTED_ERROR.lower()

    def test_placeholder_messages(self) -> None:
        """Test placeholder messages exist."""
        assert fr.MSG_BUY_NOT_IMPLEMENTED is not None
        assert fr.MSG_SELL_NOT_IMPLEMENTED is not None
        assert fr.MSG_LISTINGS_NOT_IMPLEMENTED is not None
