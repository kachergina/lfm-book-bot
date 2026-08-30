"""Tests for listing keyboards."""

from bot.keyboards.listings import (
    get_condition_keyboard,
    get_confirm_status_keyboard,
    get_description_action_keyboard,
    get_listing_manage_keyboard,
    get_listings_list_keyboard,
    get_my_listings_tabs_keyboard,
    get_photos_initial_keyboard,
    get_photos_received_keyboard,
    get_sell_confirm_keyboard,
)


class TestListingKeyboards:
    """Tests for listing keyboard functions."""

    def test_condition_keyboard(self):
        """Test condition keyboard structure."""
        keyboard = get_condition_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 6  # 5 conditions + back button
        # Check first button is "new"
        assert keyboard.inline_keyboard[0][0].callback_data == "sell:cond:new"
        # Check last button is back
        assert keyboard.inline_keyboard[-1][0].callback_data == "sell:back:price"

    def test_sell_confirm_keyboard(self):
        """Test sell confirm keyboard structure."""
        keyboard = get_sell_confirm_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 7  # publish + 5 edits + cancel
        # Check publish button
        assert keyboard.inline_keyboard[0][0].callback_data == "sell:confirm:publish"
        # Check cancel button
        assert keyboard.inline_keyboard[-1][0].callback_data == "sell:confirm:cancel"

    def test_photos_initial_keyboard(self):
        """Test photos initial keyboard has only skip button."""
        keyboard = get_photos_initial_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "sell:photos:skip"

    def test_photos_received_keyboard(self):
        """Test photos received keyboard has only done button."""
        keyboard = get_photos_received_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "sell:photos:done"

    def test_description_action_keyboard(self):
        """Test description action keyboard structure."""
        keyboard = get_description_action_keyboard()
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 1
        assert keyboard.inline_keyboard[0][0].callback_data == "sell:desc:skip"

    def test_my_listings_tabs_keyboard(self):
        """Test my listings tabs keyboard structure."""
        keyboard = get_my_listings_tabs_keyboard(
            active_count=5,
            reserved_count=2,
            sold_count=3,
            archived_count=1,
        )
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 6  # 4 tabs + new + menu
        # Check active tab has count
        assert "5" in keyboard.inline_keyboard[0][0].text
        # Check callback data
        assert keyboard.inline_keyboard[0][0].callback_data == "mylistings:tab:active"

    def test_listings_list_keyboard(self):
        """Test listings list keyboard structure."""
        listings = [
            {"id": 1, "title": "Math 6eme", "price": "15.00"},
            {"id": 2, "title": "Francais 5eme", "price": "12.00"},
        ]
        keyboard = get_listings_list_keyboard(listings, "active")
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 3  # 2 listings + back
        # Check first listing
        assert keyboard.inline_keyboard[0][0].callback_data == "mylistings:view:1"
        # Check back button
        assert keyboard.inline_keyboard[-1][0].callback_data == "mylistings:back:tabs"

    def test_listing_manage_keyboard_active(self):
        """Test listing manage keyboard for active listing."""
        keyboard = get_listing_manage_keyboard(1, "active")
        assert keyboard is not None
        # Should have edit buttons + reserve + sell + archive + back
        assert len(keyboard.inline_keyboard) >= 8
        # Check reserve button exists
        callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "ml:1:edit_photos" in callbacks
        assert "ml:1:reserve" in callbacks
        assert "ml:1:sell" in callbacks
        assert "ml:1:archive" in callbacks

    def test_listing_manage_keyboard_reserved(self):
        """Test listing manage keyboard for reserved listing."""
        keyboard = get_listing_manage_keyboard(1, "reserved")
        assert keyboard is not None
        callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        assert "ml:1:activate" in callbacks
        assert "ml:1:sell" in callbacks
        assert "ml:1:archive" in callbacks
        # Should NOT have reserve button
        assert "ml:1:reserve" not in callbacks

    def test_listing_manage_keyboard_sold(self):
        """Test listing manage keyboard for sold listing."""
        keyboard = get_listing_manage_keyboard(1, "sold")
        assert keyboard is not None
        callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
        # Should only have edit buttons and back, no status change buttons
        assert "ml:1:reserve" not in callbacks
        assert "ml:1:sell" not in callbacks
        assert "ml:1:archive" not in callbacks

    def test_confirm_status_keyboard(self):
        """Test confirm status keyboard structure."""
        keyboard = get_confirm_status_keyboard(1, "reserve")
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 2
        assert keyboard.inline_keyboard[0][0].callback_data == "ml:1:confirm:reserve"
        assert keyboard.inline_keyboard[1][0].callback_data == "ml:1:cancel"
