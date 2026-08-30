"""Tests for locale modules."""

from bot.locale import en, fr, ru


def test_new_locale_keys_exist_in_all_languages() -> None:
    """New user-facing strings must exist in FR, EN, and RU."""
    keys = [
        "CATEGORY_OTHER",
        "BUY_LISTING_DESCRIPTION",
        "SELL_ENTER_CUSTOM_TITLE",
        "BTN_EDIT_PHOTOS",
        "BTN_ADD_PHOTOS",
        "BTN_DELETE_PHOTOS",
        "MANAGE_EDIT_PHOTOS_TITLE",
        "MANAGE_DELETE_PHOTOS_PROMPT",
        "BTN_BACK_TO_MANAGE",
    ]
    for key in keys:
        assert hasattr(fr, key)
        assert hasattr(en, key)
        assert hasattr(ru, key)
        assert getattr(fr, key)
        assert getattr(en, key)
        assert getattr(ru, key)
