"""Tests for my listings handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.handlers.listings import (
    handle_confirm_status,
    handle_edit_price,
    handle_reserve,
    handle_tab_selection,
    handle_view_listing,
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


@pytest.mark.asyncio
async def test_handle_tab_selection(db_session, academic_year, user):
    """Test tab selection."""
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

    callback = _create_mock_callback("mylistings:tab:active")
    state = _create_mock_state()
    await state.set_state(ManageListingFlow.selecting_listing)

    await handle_tab_selection(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    assert callback.answer.call_count >= 1


@pytest.mark.asyncio
async def test_handle_view_listing(db_session, academic_year, user):
    """Test viewing listing details."""
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

    callback = _create_mock_callback(f"mylistings:view:{listing.id}")
    state = _create_mock_state()
    await state.set_state(ManageListingFlow.selecting_listing)

    await handle_view_listing(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == ManageListingFlow.managing


@pytest.mark.asyncio
async def test_handle_edit_price(db_session, academic_year, user):
    """Test edit price action."""
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

    callback = _create_mock_callback(f"ml:{listing.id}:edit_price")
    state = _create_mock_state()
    await state.set_state(ManageListingFlow.managing)

    await handle_edit_price(callback, state)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == ManageListingFlow.editing_price


@pytest.mark.asyncio
async def test_handle_reserve(db_session, academic_year, user):
    """Test reserve action."""
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

    callback = _create_mock_callback(f"ml:{listing.id}:reserve")
    state = _create_mock_state()
    await state.set_state(ManageListingFlow.managing)

    await handle_reserve(callback, state)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_data()
    assert state_data["pending_action"] == "reserve"


@pytest.mark.asyncio
async def test_handle_confirm_status(db_session, academic_year, user):
    """Test confirm status change."""
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

    callback = _create_mock_callback(f"ml:{listing.id}:confirm:reserve")
    state = _create_mock_state()
    await state.set_state(ManageListingFlow.managing)
    await state.update_data(listing_id=listing.id)

    await handle_confirm_status(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    callback.answer.assert_called_once()
