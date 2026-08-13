"""Tests for sell flow handler edge cases."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message, User

from bot.handlers.sell import (
    handle_condition_selection,
    handle_description_input,
    handle_description_skip,
    handle_edit_condition_from_confirm,
    handle_edit_description_from_confirm,
    handle_edit_phone_from_confirm,
    handle_edit_photos_from_confirm,
    handle_edit_price_from_confirm,
    handle_phone_input,
    handle_photo_upload,
    handle_photos_done,
    handle_photos_skip,
    handle_price_input,
)
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


class TestSellFlowEdgeCases:
    """Tests for sell flow edge cases."""

    @pytest.mark.asyncio
    async def test_handle_price_input_invalid(self):
        """Test price input with invalid value."""
        message = _create_mock_message("abc")
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_price)

        await handle_price_input(message, state)

        message.answer.assert_called_once()
        call_kwargs = message.answer.call_args
        # Should show validation error

    @pytest.mark.asyncio
    async def test_handle_price_input_no_text(self):
        """Test price input with no text."""
        message = _create_mock_message()
        message.text = None
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_price)

        await handle_price_input(message, state)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_condition_selection_invalid(self):
        """Test condition selection with invalid value."""
        callback = _create_mock_callback("sell:cond:invalid")
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_condition)

        await handle_condition_selection(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_condition_selection_no_data(self):
        """Test condition selection with no callback data."""
        callback = _create_mock_callback("")
        callback.data = None
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_condition)

        await handle_condition_selection(callback, state)

        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_phone_input_invalid(self):
        """Test phone input with invalid value."""
        message = _create_mock_message("12345")
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_phone)

        await handle_phone_input(message, state)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_phone_input_no_text(self):
        """Test phone input with no text."""
        message = _create_mock_message()
        message.text = None
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_phone)

        await handle_phone_input(message, state)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_photo_upload_no_photo(self):
        """Test photo upload with no photo."""
        message = _create_mock_message()
        message.photo = None
        state = _create_mock_state()
        await state.set_state(SellFlow.uploading_photos)

        await handle_photo_upload(message, state)

        # Should not crash

    @pytest.mark.asyncio
    async def test_handle_photos_done_no_photos(self):
        """Test photos done with no photos uploaded."""
        callback = _create_mock_callback("sell:photos:done")
        state = _create_mock_state()
        await state.set_state(SellFlow.uploading_photos)

        await handle_photos_done(callback, state)

        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_photos_skip(self):
        """Test skip photos."""
        callback = _create_mock_callback("sell:photos:skip")
        state = _create_mock_state()
        await state.set_state(SellFlow.uploading_photos)

        await handle_photos_skip(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.entering_description

    @pytest.mark.asyncio
    async def test_handle_description_input_no_text(self):
        """Test description input with no text."""
        message = _create_mock_message()
        message.text = None
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_description)

        await handle_description_input(message, state)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_description_input_too_long(self):
        """Test description input that's too long."""
        message = _create_mock_message("x" * 501)
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_description)

        await handle_description_input(message, state)

        message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_description_skip(self):
        """Test skip description."""
        callback = _create_mock_callback("sell:desc:skip")
        state = _create_mock_state()
        await state.set_state(SellFlow.entering_description)
        await state.update_data(
            book_id=1,
            book_title="Test",
            price="15.00",
            condition="good",
            phone="0612345678",
        )

        await handle_description_skip(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.confirming

    @pytest.mark.asyncio
    async def test_handle_edit_price_from_confirm(self):
        """Test edit price from confirmation screen."""
        callback = _create_mock_callback("sell:edit:price")
        state = _create_mock_state()
        await state.set_state(SellFlow.confirming)

        await handle_edit_price_from_confirm(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.entering_price

    @pytest.mark.asyncio
    async def test_handle_edit_condition_from_confirm(self):
        """Test edit condition from confirmation screen."""
        callback = _create_mock_callback("sell:edit:condition")
        state = _create_mock_state()
        await state.set_state(SellFlow.confirming)

        await handle_edit_condition_from_confirm(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.entering_condition

    @pytest.mark.asyncio
    async def test_handle_edit_phone_from_confirm(self):
        """Test edit phone from confirmation screen."""
        callback = _create_mock_callback("sell:edit:phone")
        state = _create_mock_state()
        await state.set_state(SellFlow.confirming)

        await handle_edit_phone_from_confirm(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.selecting_contact_method

    @pytest.mark.asyncio
    async def test_handle_edit_description_from_confirm(self):
        """Test edit description from confirmation screen."""
        callback = _create_mock_callback("sell:edit:description")
        state = _create_mock_state()
        await state.set_state(SellFlow.confirming)

        await handle_edit_description_from_confirm(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.entering_description

    @pytest.mark.asyncio
    async def test_handle_edit_photos_from_confirm(self):
        """Test edit photos from confirmation screen."""
        callback = _create_mock_callback("sell:edit:photos")
        state = _create_mock_state()
        await state.set_state(SellFlow.confirming)

        await handle_edit_photos_from_confirm(callback, state)

        callback.answer.assert_called_once()
        state_data = await state.get_state()
        assert state_data == SellFlow.uploading_photos
