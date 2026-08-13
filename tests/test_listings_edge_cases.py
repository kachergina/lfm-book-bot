"""Tests for listings handler edge cases and error handling."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.handlers.listings import (
    handle_activate,
    handle_archive,
    handle_confirm_status,
    handle_edit_condition,
    handle_edit_description,
    handle_edit_phone,
    handle_edit_price,
    handle_reserve,
    handle_sell,
    handle_view_listing,
)
from bot.states.fsm import ManageListingFlow


def _create_mock_callback(data: str) -> CallbackQuery:
    """Create a mock Telegram callback query."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = data
    callback.message = MagicMock(spec=Message)
    callback.message.edit_text = AsyncMock()
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456789
    return callback


def _create_mock_message(text: str = "test") -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.answer = AsyncMock()
    return message


def _create_mock_state() -> FSMContext:
    """Create a mock FSM context."""
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=MagicMock())


class TestHandleConfirmStatusEdgeCases:
    """Tests for confirm status change edge cases."""

    @pytest.mark.asyncio
    async def test_confirm_status_no_callback_data(self, db_session, academic_year, user):
        """Test confirm status with no callback data."""
        callback = _create_mock_callback("")
        callback.data = None
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=1)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert call_kwargs.kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_confirm_status_no_from_user(self, db_session, academic_year, user):
        """Test confirm status with no from_user."""
        callback = _create_mock_callback("ml:1:confirm:reserve")
        callback.from_user = None
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=1)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_status_invalid_callback_format(self, db_session, academic_year, user):
        """Test confirm status with invalid callback format."""
        callback = _create_mock_callback("ml:1:confirm")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=1)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "obsolète" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_confirm_status_no_listing_in_state(self, db_session, academic_year, user):
        """Test confirm status with no listing_id in state."""
        callback = _create_mock_callback("ml:1:confirm:reserve")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert (
            "invalides" in call_kwargs.args[0].lower()
            or "recommencer" in call_kwargs.args[0].lower()
        )

    @pytest.mark.asyncio
    async def test_confirm_status_user_not_found(self, db_session, academic_year, user):
        """Test confirm status when user not found."""
        callback = _create_mock_callback("ml:1:confirm:reserve")
        callback.from_user.id = 999999  # Non-existent user
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=1)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "non trouvé" in call_kwargs.args[0].lower()

    @pytest.mark.asyncio
    async def test_confirm_status_invalid_action(self, db_session, academic_year, user):
        """Test confirm status with invalid action."""
        callback = _create_mock_callback("ml:1:confirm:invalid")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=1)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "invalide" in call_kwargs.args[0].lower()

    @pytest.mark.asyncio
    async def test_confirm_status_listing_not_found(self, db_session, academic_year, user):
        """Test confirm status when listing not found."""
        callback = _create_mock_callback("ml:999:confirm:reserve")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=999)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "existe plus" in call_kwargs.args[0].lower()

    @pytest.mark.asyncio
    async def test_confirm_status_listing_not_owned(self, db_session, academic_year, user):
        """Test confirm status when listing belongs to another user."""
        from bot.database.repository import BookRepository, UserRepository

        book_repo = BookRepository(db_session)
        user_repo = UserRepository(db_session)

        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        other_user = await user_repo.create(telegram_id=999999999, username="other")
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=other_user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        callback = _create_mock_callback(f"ml:{listing.id}:confirm:reserve")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=listing.id)

        await handle_confirm_status(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "appartient" in call_kwargs.args[0].lower()


class TestEditHandlersEdgeCases:
    """Tests for edit handlers edge cases."""

    @pytest.mark.asyncio
    async def test_edit_price_invalid_listing_id(self):
        """Test edit price with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:edit_price")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_edit_price(callback, state)

        callback.answer.assert_called_once()
        call_kwargs = (
            callback.callback.answer.call_args
            if hasattr(callback, "callback")
            else callback.answer.call_args
        )
        # The answer should contain an error message

    @pytest.mark.asyncio
    async def test_edit_condition_invalid_listing_id(self):
        """Test edit condition with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:edit_condition")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_edit_condition(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_phone_invalid_listing_id(self):
        """Test edit phone with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:edit_phone")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_edit_phone(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_description_invalid_listing_id(self):
        """Test edit description with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:edit_desc")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_edit_description(callback, state)

        callback.answer.assert_called_once()


class TestStatusActionEdgeCases:
    """Tests for status action handlers edge cases."""

    @pytest.mark.asyncio
    async def test_reserve_invalid_listing_id(self):
        """Test reserve with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:reserve")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_reserve(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_sell_invalid_listing_id(self):
        """Test sell with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:sell")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_sell(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_invalid_listing_id(self):
        """Test activate with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:activate")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_activate(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_invalid_listing_id(self):
        """Test archive with invalid listing ID."""
        callback = _create_mock_callback("ml:abc:archive")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_archive(callback, state)

        callback.answer.assert_called_once()


class TestViewListingEdgeCases:
    """Tests for view listing edge cases."""

    @pytest.mark.asyncio
    async def test_view_listing_invalid_id(self, db_session, academic_year, user):
        """Test viewing listing with invalid ID."""
        callback = _create_mock_callback("mylistings:view:abc")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.selecting_listing)

        await handle_view_listing(callback, state, db_session)

        callback.answer.assert_called_once()
        call_kwargs = callback.answer.call_args
        assert "invalide" in call_kwargs.args[0].lower()
