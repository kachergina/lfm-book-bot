"""Tests for sell flow handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.handlers.sell import (
    handle_condition_selection,
    handle_phone_input,
    handle_price_input,
    handle_sell_book,
    handle_sell_category,
    handle_sell_grade,
    handle_sell_subject,
)
from bot.locale import fr
from bot.states.fsm import SellFlow


def _create_mock_message(text: str = "test") -> Message:
    """Create a mock Telegram message."""
    message = MagicMock(spec=Message)
    message.text = text
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.answer = AsyncMock()
    message.photo = None
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
async def test_handle_sell_category(db_session, academic_year):
    """Test category selection in sell flow."""
    callback = _create_mock_callback("buy:cat:textbook")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_category)
    await state.update_data(academic_year_id=academic_year.id)

    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await db_session.commit()

    await handle_sell_category(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.selecting_grade


@pytest.mark.asyncio
async def test_handle_sell_grade(db_session, academic_year):
    """Test grade selection in sell flow."""
    callback = _create_mock_callback("buy:grade:6ème")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_grade)
    await state.update_data(
        academic_year_id=academic_year.id,
        category="textbook",
    )

    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await db_session.commit()

    await handle_sell_grade(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.selecting_subject


@pytest.mark.asyncio
async def test_handle_sell_subject(db_session, academic_year):
    """Test subject selection in sell flow."""
    callback = _create_mock_callback("buy:subj:Mathématiques")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_subject)
    await state.update_data(
        academic_year_id=academic_year.id,
        category="textbook",
        grade="6ème",
    )

    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
        subject="Mathématiques",
    )
    await db_session.commit()

    await handle_sell_subject(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.selecting_book


@pytest.mark.asyncio
async def test_handle_sell_book(db_session, academic_year):
    """Test book selection in sell flow."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
    )
    await db_session.commit()

    callback = _create_mock_callback(f"buy:book:{book.id}")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_book)

    await handle_sell_book(callback, state, db_session)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.entering_price


@pytest.mark.asyncio
async def test_handle_price_input_valid():
    """Test valid price input."""
    message = _create_mock_message("15.00")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_price)

    await handle_price_input(message, state)

    message.answer.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.entering_condition


@pytest.mark.asyncio
async def test_handle_price_input_invalid():
    """Test invalid price input."""
    message = _create_mock_message("abc")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_price)

    await handle_price_input(message, state)

    # Should show error and stay in same state
    state_data = await state.get_state()
    assert state_data == SellFlow.entering_price


@pytest.mark.asyncio
async def test_handle_condition_selection():
    """Test condition selection."""
    callback = _create_mock_callback("sell:cond:good")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_condition)

    await handle_condition_selection(callback, state)

    callback.message.edit_text.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.selecting_contact_method


@pytest.mark.asyncio
async def test_handle_condition_selection_invalid():
    """Test invalid condition selection."""
    callback = _create_mock_callback("sell:cond:invalid")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_condition)

    await handle_condition_selection(callback, state)

    # Should show error and stay in same state
    state_data = await state.get_state()
    assert state_data == SellFlow.entering_condition


@pytest.mark.asyncio
async def test_handle_phone_input_valid():
    """Test valid phone input."""
    message = _create_mock_message("+79991234567")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_phone)

    await handle_phone_input(message, state)

    message.answer.assert_called_once()
    state_data = await state.get_state()
    assert state_data == SellFlow.uploading_photos


@pytest.mark.asyncio
async def test_handle_phone_input_invalid():
    """Test invalid phone input."""
    message = _create_mock_message("12345")
    state = _create_mock_state()
    await state.set_state(SellFlow.entering_phone)

    await handle_phone_input(message, state)

    # Should show error and stay in same state
    state_data = await state.get_state()
    assert state_data == SellFlow.entering_phone


@pytest.mark.asyncio
async def test_sell_textbook_shows_grade_step(db_session, academic_year):
    """Regression: sell textbook category continues to grade selection."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    await repo.create(
        category="textbook",
        title="Math 6eme",
        catalog_year_id=academic_year.id,
        grade_level="6ème",
    )
    await db_session.commit()

    callback = _create_mock_callback("buy:cat:textbook")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_category)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_sell_category(callback, state, db_session)

    assert await state.get_state() == SellFlow.selecting_grade
    assert callback.message.edit_text.call_args[0][0] == fr.SELL_SELECT_GRADE


@pytest.mark.asyncio
async def test_sell_literature_skips_to_books_without_grade(db_session, academic_year):
    """Regression: literature books without grade go directly to book list."""
    from bot.database.repository import BookRepository

    repo = BookRepository(db_session)
    book = await repo.create(
        category="literature",
        title="Le Petit Prince",
        catalog_year_id=academic_year.id,
        grade_level=None,
        subject="Littérature",
    )
    await db_session.commit()

    callback = _create_mock_callback("buy:cat:literature")
    state = _create_mock_state()
    await state.set_state(SellFlow.selecting_category)
    await state.update_data(academic_year_id=academic_year.id)

    await handle_sell_category(callback, state, db_session)

    assert await state.get_state() == SellFlow.selecting_book
    markup = callback.message.edit_text.call_args[1]["reply_markup"]
    assert markup.inline_keyboard[0][0].callback_data == f"buy:book:{book.id}"


def test_sell_category_keyboard_uses_buy_callbacks():
    """Regression: sell category keyboard matches sell handler callback prefix."""
    from bot.keyboards.catalog import get_sell_category_keyboard

    keyboard = get_sell_category_keyboard()
    assert keyboard.inline_keyboard[0][0].callback_data == "buy:cat:textbook"
    assert keyboard.inline_keyboard[1][0].callback_data == "buy:cat:literature"
