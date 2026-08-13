"""Tests for listings handler additional coverage."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.handlers.listings import (
    handle_back_to_listings_from_manage,
    handle_back_to_menu,
    handle_cancel_status,
    handle_condition_input,
    handle_description_input,
    handle_phone_input,
    handle_price_input,
    handle_tab_selection,
)
from bot.states.fsm import ManageListingFlow


def _create_mock_message(text: str = "test") -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.answer = AsyncMock()
    return message


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


def _create_mock_state() -> FSMContext:
    """Create a mock FSM context."""
    storage = MemoryStorage()
    return FSMContext(storage=storage, key=MagicMock())


class TestListingsHandlerAdditional:
    """Tests for listings handler additional coverage."""

    @pytest.mark.asyncio
    async def test_handle_tab_selection_no_data(self, db_session, academic_year, user):
        """Test tab selection with no callback data."""
        callback = _create_mock_callback("")
        callback.data = None
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.selecting_listing)

        await handle_tab_selection(callback, state, db_session)

        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_price_input_valid(self, db_session, academic_year, user):
        """Test valid price input for editing."""
        from bot.database.repository import BookRepository

        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        message = _create_mock_message("20.00")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_price)
        await state.update_data(listing_id=listing.id)

        await handle_price_input(message, state, db_session)

        message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_price_input_invalid_value(self, db_session, academic_year, user):
        """Test invalid price input for editing."""
        message = _create_mock_message("abc")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_price)
        await state.update_data(listing_id=1)

        await handle_price_input(message, state, db_session)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_phone_input_valid(self, db_session, academic_year, user):
        """Test valid phone input for editing."""
        from bot.database.repository import BookRepository

        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        message = _create_mock_message("0798765432")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_phone)
        await state.update_data(listing_id=listing.id)

        await handle_phone_input(message, state, db_session)

        message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_phone_input_invalid_value(self, db_session, academic_year, user):
        """Test invalid phone input for editing."""
        message = _create_mock_message("12345")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_phone)
        await state.update_data(listing_id=1)

        await handle_phone_input(message, state, db_session)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_description_input_valid(self, db_session, academic_year, user):
        """Test valid description input for editing."""
        from bot.database.repository import BookRepository

        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        message = _create_mock_message("New description")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_description)
        await state.update_data(listing_id=listing.id)

        await handle_description_input(message, state, db_session)

        message.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_condition_input_valid(self, db_session, academic_year, user):
        """Test valid condition input for editing."""
        from bot.database.repository import BookRepository

        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        callback = _create_mock_callback("sell:cond:new")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_condition)
        await state.update_data(listing_id=listing.id)

        await handle_condition_input(callback, state, db_session)

        callback.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_condition_input_invalid(self, db_session, academic_year, user):
        """Test invalid condition input for editing."""
        callback = _create_mock_callback("sell:cond:invalid")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.editing_condition)
        await state.update_data(listing_id=1)

        await handle_condition_input(callback, state, db_session)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancel_status(self, db_session, academic_year, user):
        """Test cancel status change."""
        from bot.database.repository import BookRepository

        book_repo = BookRepository(db_session)
        book = await book_repo.create(
            category="textbook",
            title="Math 6eme",
            catalog_year_id=academic_year.id,
        )
        await db_session.commit()

        from bot.database.models import Listing

        listing = Listing(
            book_id=book.id,
            seller_id=user.id,
            academic_year_id=academic_year.id,
            price=15.00,
            condition="good",
            status="active",
            contact_phone="0612345678",
        )
        db_session.add(listing)
        await db_session.commit()

        callback = _create_mock_callback(f"ml:{listing.id}:cancel")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)
        await state.update_data(listing_id=listing.id)

        await handle_cancel_status(callback, state, db_session)

        callback.answer.assert_called()

    @pytest.mark.asyncio
    async def test_handle_back_to_menu(self, db_session, academic_year, user):
        """Test back to main menu."""
        callback = _create_mock_callback("mylistings:menu")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.selecting_listing)

        await handle_back_to_menu(callback, state)

        callback.answer.assert_called()
        state_data = await state.get_state()
        assert state_data is None

    @pytest.mark.asyncio
    async def test_handle_back_to_listings_from_manage(self, db_session, academic_year, user):
        """Test back to listings from management view."""
        callback = _create_mock_callback("mylistings:tab:active")
        state = _create_mock_state()
        await state.set_state(ManageListingFlow.managing)

        await handle_back_to_listings_from_manage(callback, state, db_session)

        callback.answer.assert_called()
        state_data = await state.get_state()
        assert state_data == ManageListingFlow.selecting_listing
